"""Голосовой движок: микрофон -> wake word -> VAD -> Whisper -> команда.

Конвейер обработки одного кадра аудио:

    1. sounddevice отдаёт блок 512 сэмплов в ``audio_callback``;
    2. пока не услышана фраза-активатор, каждый блок уходит в Vosk
       (``is_wake_word``);
    3. после активации Silero VAD решает, есть ли в кадре речь, и копит
       кадры в буфер;
    4. после ~1 секунды тишины буфер уходит в Whisper;
    5. распознанный текст передаётся в ``core.action_definition``.
"""

import json
import os
import queue
import site
import sys
import time
import threading
from pathlib import Path

import numpy as np
import sounddevice as sd
import torch
from vosk import KaldiRecognizer, Model

import core.action_definition as ad
import faster_whisper as fw

# ---------------------------------------------------------------------------
# Аудио
# ---------------------------------------------------------------------------

SAMPLE_RATE = 16_000        # 16 кГц — требование Whisper, Vosk и Silero VAD
CHANNELS = 1
BLOCK_SIZE = 512            # 512 сэмплов = 32 мс при 16 кГц

SPEECH_THRESHOLD = 0.5      # Silero VAD: выше порога кадр считается речью
SILENCE_BLOCKS = 34         # 34 * 32 мс ≈ 1.1 с тишины завершают фразу
WAKE_TIMEOUT = 20.0         # Время ожидания команды

# ---------------------------------------------------------------------------
# Пути
# ---------------------------------------------------------------------------

CORE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CORE_DIR.parent

WHISPER_MODEL_DIR = CORE_DIR / "faster-whisper-large-v3-turbo-ct2"
VOSK_MODEL_DIR = CORE_DIR / "vosk-model-small-ru-0.22"
SETTINGS_PATH = PROJECT_DIR / "setting_user.json"


# ---------------------------------------------------------------------------
# Окружение
# ---------------------------------------------------------------------------

def _register_cuda_dlls() -> None:
    """Добавляет DLL cuBLAS/cuDNN из user-site в PATH (нужно только на Windows)."""
    if sys.platform != "win32":
        return

    user_packages = site.getusersitepackages()
    for package in ("cudnn", "cublas"):
        dll_dir = os.path.join(user_packages, "nvidia", package, "bin")
        if os.path.exists(dll_dir):
            os.environ["PATH"] = dll_dir + os.pathsep + os.environ.get("PATH", "")
            os.add_dll_directory(dll_dir)


def _silero_vad_repo() -> str:
    """Ищет silero-vad: папка core/silero-vad -> кэш torch.hub -> GitHub."""
    local_repo = CORE_DIR / "silero-vad"
    if (local_repo / "hubconf.py").exists():
        return str(local_repo)

    hub_cache = Path.home() / ".cache" / "torch" / "hub" / "snakers4_silero-vad_master"
    if (hub_cache / "hubconf.py").exists():
        return str(hub_cache)

    return "snakers4/silero-vad"


_register_cuda_dlls()
SILERO_VAD_REPO = _silero_vad_repo()

with open(SETTINGS_PATH, encoding="utf-8") as file:
    INPUT_DEVICE = json.load(file)["input_device"]

# ---------------------------------------------------------------------------
# Wake word (заготовка)
# ---------------------------------------------------------------------------
with open(SETTINGS_PATH,encoding="utf-8") as file:
    name_asistent = json.load(file)["name_asistet"]

WAKE_PHRASES = [
    f"привет {name_asistent}",
    f"{name_asistent}",
]

wake_model = Model(str(VOSK_MODEL_DIR))
wake_rec = KaldiRecognizer(wake_model, SAMPLE_RATE)

# Очередь команд: сейчас её никто не наполняет, поток _worker() ждёт вхолостую.
command_queue: queue.Queue[str] = queue.Queue()


def is_wake_word(pcm_chunk: bytes) -> bool:
    """Проверяет, прозвучала ли фраза-активатор в очередном куске PCM."""
    if wake_rec.AcceptWaveform(pcm_chunk):
        text = json.loads(wake_rec.Result()).get("text", "")
        return any(phrase in text for phrase in WAKE_PHRASES)

    partial = json.loads(wake_rec.PartialResult()).get("partial", "")
    return any(phrase in partial for phrase in WAKE_PHRASES)


# ---------------------------------------------------------------------------
# Движок
# ---------------------------------------------------------------------------

class Voice_enginer:
    """Слушает микрофон, распознаёт фразу и передаёт её обработчику команд."""

    def __init__(self) -> None:
        self.whisper_model = fw.WhisperModel(
            str(WHISPER_MODEL_DIR),
            device="cuda",
            compute_type="int8_float16",
        )

        self.vad_model, self.vad_utils = torch.hub.load(
            source="local",
            repo_or_dir=SILERO_VAD_REPO,
            model="silero_vad",
        )
        (
            self.get_speech_timestamps,
            _,
            self.read_audio,
            _,
            _,
        ) = self.vad_utils
        self.wake_word = False
        self._reset_capture()
        print("Все готово к работе")

    # ------------------------------------------------------------- запись

    def _check_wake_timeout(self) -> None:
        """Забывает активацию, если команда так и не прозвучала."""
        if self.wake_word and time.monotonic() > self._wake_deadline:
            self.wake_word = False
            wake_rec.Reset()


    def prolongation(self) -> None:
        self._wake_deadline  = time.monotonic() + WAKE_TIMEOUT


    def audio_callback(self, indata, frames_count, time_info, status) -> None:
        """Колбэк sounddevice: получает один блок аудио и решает, что с ним делать.

        Параметры ``frames`` и ``time`` не используются — они нужны только
        для совместимости с сигнатурой колбэка.
        """
        audio_frame = np.frombuffer(indata, dtype=np.float32)

        # Silero VAD ждёт тензор и возвращает вероятность речи в кадре
        audio_tensor = torch.from_numpy(audio_frame)
        speech_prob = self.vad_model(audio_tensor, SAMPLE_RATE).item()

        if not self.wake_word:
            pcm = (audio_frame * 32767).astype(np.int16).tobytes()
            if is_wake_word(pcm):
                self.wake_word = True
                self._wake_deadline = time.monotonic() + WAKE_TIMEOUT
                wake_rec.Reset()

        self._check_wake_timeout()

        if speech_prob > SPEECH_THRESHOLD and self.wake_word:
            self._buffer_speech(audio_frame)
        else:
            self._track_silence(audio_frame)

    def _buffer_speech(self, audio_frame: np.ndarray) -> None:
        """Копит кадры речи и сбрасывает счётчик тишины."""
        if not self.speech_status:
            print("Запись идет")
            self.speech_status = True

        self.audio_buffer.append(audio_frame.copy())
        self.silence_counter = 0

    def _track_silence(self, audio_frame: np.ndarray) -> None:
        """Считает тишину и закрывает фразу, когда её накопилось достаточно."""
        self.silence_counter += 1

        if not self.speech_status:
            return

        self.audio_buffer.append(audio_frame.copy())
        if self.silence_counter > SILENCE_BLOCKS:
            self._process_utterance()

    def _reset_capture(self) -> None:
        """Готовит состояние записи к следующей фразе."""
        self.audio_buffer: list[np.ndarray] = []
        self.speech_status = False
        self.silence_counter = 0

    # -------------------------------------------------------- распознавание

    def _process_utterance(self) -> None:
        """Склеивает буфер, распознаёт речь и передаёт текст обработчику команд."""
        if not self.audio_buffer:
            return

        full_audio = np.concatenate(self.audio_buffer)

        self._reset_capture()
        print("Запись окончена")

        segments, _ = self.whisper_model.transcribe(
            full_audio,
            beam_size=5,
        )
        result = "".join(segment.text for segment in segments)

        if result:
            print(f"команда отправлена:{result}")
            ad.command_processing(result)

    def _worker(self) -> None:
        """Поток-потребитель ``command_queue`` (очередь пока не наполняется)."""
        while True:
            text = command_queue.get()
            ad.command_processing(text)
            command_queue.task_done()

    # ---------------------------------------------------------- управление

    def voise_assistent(self, stats_voise_asistent: bool) -> None:
        """Включает или выключает прослушивание микрофона."""
        if stats_voise_asistent:
            self._stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                blocksize=BLOCK_SIZE,
                dtype="float32",
                device=INPUT_DEVICE,
                callback=self.audio_callback,
            )

            self._stream.start()
            self.is_running = True
            print("Активирована запись с микрофона")
            threading.Thread(target=self._worker, daemon=True).start()
        else:
            self._stream.stop()
            self._stream.close()
            self.is_running = False
            print("Запись с микрофона закончена")
