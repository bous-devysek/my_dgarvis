import sys
import faster_whisper as fw
import sounddevice as sd
import numpy as np
import torch
import command 

SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_SIZE = 512

model_size = 'base'

def check_devaice():
    print(sd.query_devices())


class Voice_enginer:
    def __init__(self):
        self.whisper_model = fw.WhisperModel(model_size,
                     device='cuba',
                     compute_type='float32')

        self.vad_model = torch.hub.load(repo_or_dir='snakers4/silero-vad', 
                                        model='silero_vad')
        (self.get_speech_timestamps, _, self.read_audio, _, _) = self.utils

        self.audio_buffer = []
        self.speeck_status = False
        self.silence_counter = 0
        print('все готово к работе')

    
    def audio_callbak(self,indata, frames, time, status)->None:
        # Превращает входящий поток в массив float32
        audio_frame = np.frombuffer(indata,dtype=np.float32)

        # Переводит аудио-фрейм в тензор PyTorch для нейросети VAD
        audio_tensor = torch.from_numpy(audio_frame)

        # Оценивает вероятность того, что говорит человек
        speech_prob = self.vad_model(audio_tensor, SAMPLE_RATE).item()

        if speech_prob > 0.5:
            if not self.speeck_status:
                print('запись идет')
                self.speeck_status = True

            self.audio_buffer.append(audio_frame.copy())
            self.silence_counter = 0

        else:
            self.silence_counter += 1
            if self.silence_counter >= 35:
                print('запись окончена')
                self.process_cached_audio()


    def process_cached_audio(self):
        if not self.audio_buffer:
            return
            
        full_audio = np.concatenate(self.audio_buffer)

        self.audio_buffer = []
        self.is_speaking = False
        self.silence_counter = 0

        segments,_ = self.whisper_model.transcribe(full_audio,beam_size=5,language='ru')

        result_text = ''
        for segment in segments:
            result_text += segment.text

        if result_text:
            print(result_text)


    def voise_asistent(self):
        print('запись пошла')
        # активируем запись с микрофона
        self.steam = sd.InputStream(samplerate=SAMPLE_RATE,
                                channels=CHANNELS,
                                blocksize=8000,
                                dtype='float32',
                                device=1,
                                callback=self.audio_callbak)

Voice = Voice_enginer()
if __name__ == '__main__':
    Voice.voise_asistent()