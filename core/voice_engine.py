import faster_whisper as fw
import sounddevice as sd
import queue
from vosk import Model, KaldiRecognizer
import json

audio_queue = queue.Queue()

simple_rate = 16000
channelss = 1

model = Model(model_name="vosk-model-small-ru-0.22")

def audio_callbak(indata, frames, time, status)->None:
    audio_queue.put(bytes(indata))


def check_devaice():
    print(sd.query_devices())


def voise_asistent():
    print('запись пошла')
    # активируем запись с микрофона
    steam = sd.InputStream(samplerate=simple_rate,
                            channels=channelss,
                            blocksize=16000,
                            dtype='int16',
                            device=1,
                            callback=audio_callbak)
    #активируем распознователь текста
    recognizer = KaldiRecognizer(model, simple_rate)

    with steam:
        while True:
            data = audio_queue.get()

            if recognizer.AcceptWaveform(data):
                # Метод AcceptWaveform вернет True, если Vosk ПОНЯЛ, что вы закончили фразу!
                result_json = recognizer.Result()
                result_data = json.loads(result_json)
                text = result_data.get("text", "")
                
                if text:
                    print(f"Вы сказали: {text}")

                if text == 'стоп':
                    break

            else:
                # Если человек еще говорит, Vosk выдает промежуточные (неполные) результаты
                partial_json = recognizer.PartialResult()
                partial_data = json.loads(partial_json)
                partial_text = partial_data.get("partial", "")
                if partial_text:
                    # Выводим текст в одну строку на лету
                    print(f"\Слушаю: {partial_text}", end="", flush=True)


if __name__ == '__main__':
    voise_asistent()