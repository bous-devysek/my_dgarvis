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

import ctypes
import json
import os
import queue
import site
import sys
import time
import threading
import traceback
from pathlib import Path
from collections import deque

import numpy as np
import sounddevice as sd
import torch
from vosk import KaldiRecognizer, Model

import core.action_definition as ad
import faster_whisper as fw
from silero_vad import load_silero_vad

# ---------------------------------------------------------------------------
# Аудио
# ---------------------------------------------------------------------------

SAMPLE_RATE = 16_000        # 16 кГц — требование Whisper, Vosk и Silero VAD
CHANNELS = 1
BLOCK_SIZE = 512            # 512 сэмплов = 32 мс при 16 кГц

SPEECH_THRESHOLD = 0.5     # Silero VAD: выше порога кадр считается речью
SILENCE_BLOCKS = 34         # 34 * 32 мс ≈ 1.1 с тишины завершают фразу
WAKE_TIMEOUT = 30.0         # Время ожидания команды
PRE_ROLL_BLOCKS = 32        # Буфер перезаписи
MAX_UTTERANCE_BLOCKS =30*10 #Максимальный буфер
MIN_SPEECH_SEC = 0.3
MIN_SPEECH_RATIO = 0.3
asr_q = queue.Queue()

# ---------------------------------------------------------------------------
# Пути
# ---------------------------------------------------------------------------

CORE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = CORE_DIR.parent

WHISPER_MODEL_DIR = CORE_DIR.parent / "models" / "faster-whisper-large-v3-turbo-ct2"
VOSK_MODEL_DIR = PROJECT_DIR / "models" / "vosk-model-small-ru-0.22"
SETTINGS_PATH = PROJECT_DIR / "config" / "setting_user.json"


# ---------------------------------------------------------------------------
# Окружение
# ---------------------------------------------------------------------------
def _vosk_path(path: Path) -> str:
    if sys.platform != "win32":
        return str(path)
    buf = ctypes.create_unicode_buffer(32768)
    length = ctypes.windll.kernel32.GetShortPathNameW(str(path), buf, len(buf))
    return buf.value if length else str(path)


def _register_cuda_dlls() -> None:
    if sys.platform != "win32":
        return

    roots = {site.getusersitepackages(), *site.getsitepackages(), sys.prefix}
    for root in roots:
        for package in ("cudnn", "cublas"):
            dll_dir = Path(root) / "nvidia" / package / "bin"
            if not dll_dir.is_dir():
                continue
            os.environ["PATH"] = str(dll_dir) + os.pathsep + os.environ.get("PATH", "")
            try:
                os.add_dll_directory(str(dll_dir))
            except OSError:
                pass


wake_model = Model(_vosk_path(VOSK_MODEL_DIR))

_register_cuda_dlls()
with open(SETTINGS_PATH, encoding="utf-8") as file:
    settings = json.load(file)

INPUT_DEVICE = settings["input_device"]
name_asistent = settings["name_asistet"]

# ---------------------------------------------------------------------------
# Wake word (заготовка)
# ---------------------------------------------------------------------------

WAKE_PHRASES = [
    f"привет {name_asistent}",
    f"{name_asistent}",
]

wake_rec = KaldiRecognizer(wake_model, SAMPLE_RATE)

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
        self.vad_model = load_silero_vad()

        self.wake_word = False
        self._wake_deadline = 0.0

        self.pre_roll = deque(maxlen=PRE_ROLL_BLOCKS)
        self.utterance: list[np.ndarray] = []
        self.speaking = False
        self.silence = 0
        self.speech_frames = 0
        self.speech_start = 0
        self.last_speech = 0

        self._worker_thread = None
        self._stream = None

        self._reset_capture()
        print("Все готово к работе")


    # ------------------------------------------------------------- запись
    def audio_callback(self, indata, frames_count, time_info, status) -> None:
        """Колбэк sounddevice: получает один блок аудио и решает, что с ним делать.
        Параметры ``frames`` и ``time`` не используются.""" 
        try:
            audio_frame = np.frombuffer(indata, dtype=np.float32).reshape(-1)

            # Silero VAD возвращает вероятность речи в кадре
            speech_prob = self.vad_model(torch.from_numpy(audio_frame),SAMPLE_RATE).item()
            self.pre_roll.append(audio_frame.copy())
            if not self.wake_word:
                pcm = (audio_frame * 32767).astype(np.int16).tobytes()
                if is_wake_word(pcm):
                    self.wake_word = True
                    self._wake_deadline = time.monotonic() + WAKE_TIMEOUT
                    wake_rec.Reset()
                    self._reset_capture()
                return

            self._check_wake_timeout()
            if not self.wake_word:
                return
            
            self.process_frame(audio_frame.copy(), speech_prob)
        except Exception:
            print('Ошибка')
    
    #------------------------------------------------------------------- функции к записи
    def process_frame(self,frame,speech_prod):
        self.pre_roll.append(frame)

        if not self.speaking:
            if speech_prod > SPEECH_THRESHOLD:
                self.speaking = True
                self.silence = 0
                self.utterance = list(self.pre_roll)
                self.speech_start = len(self.utterance) - 1
                self.last_speech = self.speech_start
                self.speech_frames = 1
            return
        
        self.utterance.append(frame.copy())

        if speech_prod > SPEECH_THRESHOLD: 
            self.silence = 0
            self.speech_frames += 1
            self.last_speech = len(self.utterance) - 1
        else: self.silence += 1

        if self.silence > SILENCE_BLOCKS or len(self.utterance) > MAX_UTTERANCE_BLOCKS:
            audio = np.concatenate(self.utterance)
            speech_regions = self.last_speech - self.speech_start + 1
            metrics = (audio, self.speech_frames, speech_regions)
            self._reset_capture()
            print("Запись окончена и добавлена в очередь")
            asr_q.put(metrics)


    def _check_wake_timeout(self) -> None:
        """Забывает активацию, если команда так и не прозвучала."""
        if self.wake_word and time.monotonic() > self._wake_deadline:
            self.wake_word = False
            wake_rec.Reset()
            self._reset_capture()


    def prolongation(self) -> None:
        self._wake_deadline  = time.monotonic() + WAKE_TIMEOUT


    def _reset_capture(self) -> None:
        """Готовит состояние записи к следующей фразе."""
        self.pre_roll.clear()
        self.utterance = []
        self.speaking = False
        self.silence = 0
        self.speech_frames = 0
        self.speech_start = 0
        self.last_speech = 0
        self.vad_model.reset_states()


    def _has_enough_speech(self, speech_blocks: int, region_blocks: int) -> bool:
        speech_dur = speech_blocks * BLOCK_SIZE / SAMPLE_RATE
        ratio = speech_blocks / region_blocks if region_blocks > 0 else 0.0
        return speech_dur >= MIN_SPEECH_SEC and ratio >= MIN_SPEECH_RATIO


    # -------------------------------------------------------- распознавание

    def _process_utterance(self, audio, speech_blocks: int, region_blocks: int) -> None:
        """Склеивает буфер, распознаёт речь и передаёт текст обработчику команд."""

        if not self._has_enough_speech(speech_blocks, region_blocks):
            print("В буфере почти нет речи")
            return

        segments, _ = self.whisper_model.transcribe(
            audio,
            beam_size=5,
            condition_on_previous_text=False,
            no_speech_threshold=0.6,
            log_prob_threshold=-1.0,
            compression_ratio_threshold=2.4,
            vad_filter=False
        )
        result = "".join(segment.text for segment in segments)

        if result:
            print(f"команда отправлена:{result}")
            self.status_comad = ad.command_processing(result)
            if self.status_comad:
                self.prolongation()


    def _worker(self) -> None:
        while True:
            audio, speech_blocks, region_blocks = asr_q.get()
            try:
                self._process_utterance(audio, speech_blocks, region_blocks)
            except Exception:
                traceback.print_exc()
            finally:
                asr_q.task_done()

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
            if self._worker_thread is None or not self._worker_thread.is_alive():
                self._worker_thread = threading.Thread(target=self._worker, daemon=True)
                self._worker_thread.start()
        else:
            self._stream.stop()
            self._stream.close()
            self.is_running = False
            self.wake_word = False
            self._wake_deadline = 0.0
            self._reset_capture()
            wake_rec.Reset()
            print("Запись с микрофона закончена")