import os

def open_brauser():
    if os.path.exists("C:/Program Files/Mozilla Firefox"):
        os.system('"C:/Program Files/Mozilla Firefox/firefox.exe"')
    else:
        print('нихуя нету')
