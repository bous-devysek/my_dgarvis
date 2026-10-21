import os
import sys
import faster_whisper as fw
import sounddevice as sd
import numpy as np
import torch
import core.model_inference as mi

SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_SIZE = 512
CD_TYPE = ''

#капелька вайп кодинга
if sys.platform == "win32":
    import site
    user_packages = site.getusersitepackages()
    
    # Путь к cublas и cudnn в вашем окружении (как на скриншоте)
    cublas_path = os.path.join(user_packages, "nvidia", "cublas", "bin")
    cudnn_path = os.path.join(user_packages, "nvidia", "cudnn", "bin")
    
    if os.path.exists(cublas_path):
        os.add_dll_directory(cublas_path)
    if os.path.exists(cudnn_path):
        os.add_dll_directory(cudnn_path)
# тут он заканчивается

model_size = 'C:/Users/bous_devysek/Desktop/my_gravis/core/faster-whisper-small'

def check_devaice():
    print(sd.query_devices())


# класс для распознания, обработке и выполнения команд
class Voice_enginer:
    # создание основных переменных и распаковка модели
    def __init__(self):
        self.whisper_model = fw.WhisperModel(model_size,
                     device='cuda',
                     compute_type='float32')


        self.vad_model, self.utils = torch.hub.load(repo_or_dir='snakers4/silero-vad', 
                                        model='silero_vad',)
        (self.get_speech_timestamps, _, self.read_audio, _, _) = self.utils

        self.audio_buffer = []
        self.speeck_status = False
        self.silence_counter = 0
        print('все готово к работе')

    
    def audio_callback(self,indata, frames, time, status)->None:
        # Превращает входящий поток в кусочки для масива float16
        audio_frame = np.frombuffer(indata,dtype=np.float32)

        # Переводит аудио-фрейм в тензор PyTorch для нейросети VAD
        audio_tensor = torch.from_numpy(audio_frame)

        # Оценивает вероятность того, что говорит человек
        speech_prob = self.vad_model(audio_tensor, SAMPLE_RATE).item()

        # если веротность больше 0.5 то программа начинает запись и оканчивает если пользователь молчит больше 1 сек +-
        if speech_prob > 0.5:
            if not self.speeck_status:
                print('запись идет')
                self.speeck_status = True

            # добовляем куски пока пользоваьель говорит, и сбрасуем статус молчания до 0
            self.audio_buffer.append(audio_frame.copy())
            self.silence_counter = 0

        else:
            self.silence_counter += 1
            if self.speeck_status == True:
                self.audio_buffer.append(audio_frame.copy())
                if self.silence_counter > 34:
                    self.process_cached_audio()


    #переводит весь масив в речь и вызываем команду если она есть
    def process_cached_audio(self):
        if not self.audio_buffer:
            return
            
        full_audio = np.concatenate(self.audio_buffer)

        self.audio_buffer = []
        self.speeck_status = False
        self.silence_counter = 0

        print('запись окончена')

        segments,_ = self.whisper_model.transcribe(full_audio,beam_size=5,language='ru')

        result = ''
        for segment in segments:
            result += segment.text

        if result:
            print(result)
            mi.defining_invoking_commands(result)


    def voise_asistent(self):
        print('активирована запись с микрофона')
        # активируем запись с микрофона
        self.steam = sd.InputStream(samplerate=SAMPLE_RATE,
                                channels=CHANNELS,
                                blocksize=BLOCK_SIZE,
                                dtype='float32',
                                device=1,
                                callback=self.audio_callback)
        self.steam.start()

    