import os,sys,torch,queue,json,threading
import sounddevice as sd
import numpy as np
from pathlib import Path
import core.action_definition as ad

SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_SIZE = 512
CD_TYPE = ''

q = queue.Queue(maxsize=0)
stats_voise_asistent = False

model_size = os.path.join(os.path.dirname(__file__), 'faster-whisper-small')
import faster_whisper as fw

#капелька вайп кодинга
if sys.platform == "win32":
    import site
    user_packages = site.getusersitepackages()
    cublas_path = os.path.join(user_packages, "nvidia", "cublas", "bin")
    cudnn_path = os.path.join(user_packages, "nvidia", "cudnn", "bin")

    for p in (cudnn_path, cublas_path):
        if os.path.exists(p):
            os.environ["PATH"] = p + os.pathsep + os.environ.get("PATH", "")
            os.add_dll_directory(p)

# Порядок поиска: папка core/silero-vad -> кэш torch.hub -> скачивание с GitHub.
silero_vad_repo = os.path.join(os.path.dirname(__file__), 'silero-vad')
if not os.path.exists(os.path.join(silero_vad_repo, 'hubconf.py')):
    hub_cache = os.path.join(os.path.expanduser('~'), '.cache', 'torch', 'hub', 'snakers4_silero-vad_master')
    silero_vad_repo = hub_cache if os.path.exists(os.path.join(hub_cache, 'hubconf.py')) else 'snakers4/silero-vad'
# тут он заканчивается

path_setting = Path(__file__).resolve().parent.parent / "setting_user.json"

# Чтение активного микрофона
with open(path_setting) as file:
    setting = json.load(file)
    input_device = setting["input_device"]

# класс для распознания, обработке и выполнения команд
class Voice_enginer:
    # создание основных переменных и распаковка модели
    def __init__(self):
        self.whisper_model = fw.WhisperModel(model_size,
                    device='cuda',
                    compute_type='float32')


        self.vad_model, self.utils = torch.hub.load(
                                        source='local',
                                        repo_or_dir=silero_vad_repo, 
                                        model='silero_vad',)
        (self.get_speech_timestamps, _, self.read_audio, _, _) = self.utils

        self.audio_buffer = []
        self.speech_status = False
        self.silence_counter = 0
        print('Все готово к работе')

    
    def audio_callback(self,indata, frames, time, status)->None:
        # Превращает входящий поток в кусочки для масива float16
        audio_frame = np.frombuffer(indata,dtype=np.float32)

        # Переводит аудио-фрейм в тензор PyTorch для нейросети VAD
        audio_tensor = torch.from_numpy(audio_frame)

        # Оценивает вероятность того, что говорит человек
        speech_prob = self.vad_model(audio_tensor, SAMPLE_RATE).item()

        #print(f"-Шанс-что-вы-говорите-{speech_prob*100}%------")
        # если веротность больше 90% то программа начинает запись и оканчивает если пользователь молчит больше 1 сек +-
        if speech_prob > 0.9:
            if not self.speech_status:
                print('Запись идет')
                self.speech_status = True

            # добовляем куски пока пользоваьель говорит, и сбрасуем статус молчания до 0
            self.audio_buffer.append(audio_frame.copy())
            self.silence_counter = 0

        else:
            self.silence_counter += 1
            if self.speech_status == True:
                self.audio_buffer.append(audio_frame.copy())
                if self.silence_counter > 34:
                    self.process_cached_audio()

    
    def worker(self):
        while True:
            text = q.get()
            ad.command_processing(text)
            q.task_done()


    #переводит весь масив в речь и вызываем команду если она есть
    def process_cached_audio(self):
        if not self.audio_buffer:
            return
            
        full_audio = np.concatenate(self.audio_buffer)

        self.audio_buffer = []
        self.speech_status = False
        self.silence_counter = 0
        print('Запись окончена')
        segments,_ = self.whisper_model.transcribe(full_audio,beam_size=5)

        result = ''
        for segment in segments:
            result += segment.text

        if result:
            print(f'команда отправлена:{result}')  
            ad.command_processing(result)


    def voise_assistent(self):
        print('активирована запись с микрофона')
        # активируем запись с микрофона
        self.steam = sd.InputStream(samplerate=SAMPLE_RATE,
                                channels=CHANNELS,
                                blocksize=BLOCK_SIZE,
                                dtype='float32',
                                device=input_device,
                                callback=self.audio_callback)
        
        if not stats_voise_asistent:
            self.steam.start()
            threading.Thread(target=self.worker, daemon= True).start()
        else:
            self.steam.stop()
