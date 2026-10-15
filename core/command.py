import os

def open_brauser():
    if os.path.exists("C:/Program Files/Mozilla Firefox"):
        os.system('"C:/Program Files/Mozilla Firefox/firefox.exe"')
    else:
        print('нихуя нету')


def request_filtering(input_text):
    input_text = input_text.strip()
    if input_text[-1] == '.':
        input_text = input_text[:-1]
    output_text = input_text
    return output_text


# простая реализация проверки на имеющиеся команды для теста
def command_recognition(command_text):
    dict_command = {
        'открой браузер': open_brauser
    }

    command_text = request_filtering(command_text)

    print(f'{repr(command_text)} {dict_command.keys()}')
    if command_text in dict_command.keys():
        dict_command[command_text]()

if __name__ == '__main__':
    command_recognition('открой браузер')