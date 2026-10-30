import customtkinter as ctk
import winreg
import sys
import json
import os
import sounddevice as sd

ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('dark-blue')

APP_NAME = 'garvis'
REG_PATH = r'Software\Microsoft\Windows\CurrentVersion\Run'

standard_user_setting = {
    "name_user":'',
    "stats_auto_load":0,
    "input_device": None,
    }

# Основной интерфейс приложения / interface
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.setting()
        self.geometry('720x480')
        self.button = ctk.CTkCheckBox(master=self, 
                                text='auto load program',
                                command=self.auto_load)
        self.swith = ctk.CTkSwitch(master=self,
                                        text = 'start',
                                        command=self.stream_start)
        if self.temp_data['stats_auto_load']:
            self.button.select()
        else:
            self.button.deselect()

        if not self.temp_data["input_device"]:
            input_device,_ = sd.default.device 
            self.save_settings("input_device",input_device)


    #Чтение настроек пользователя/или их создание в противном случае
    def setting(self):
        path_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'setting_user.json')
        try:
            with open(path_json,'r',encoding='utf-8') as file:
                self.temp_data = json.load(file)

        except FileNotFoundError:
            with open(path_json,'w',encoding='utf-8') as file:
                json.dump(standard_user_setting,file,indent=4,ensure_ascii=False)
            self.temp_data = standard_user_setting


    def main_menu(self):
        self.button.place(x=50,y=400-10)
        self.swith.place(x=450,y=400-10)


    #функция отвечающая за запись голоса
    def stream_start(self):
        self.status_asistent = self.swith.get()
        Voice.voise_assistent(self.status_asistent)


    # Фукция для изменения состояния автозапуска программы / avto load program
    def auto_load(self):
        print('статус auto-load изменен')
        status = self.button.get()
        self.save_settings('stats_auto_load',status)
        app_path = f'"{sys.executable}" "{__file__}"'
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,REG_PATH,0,winreg.KEY_WRITE)
        except OSError:
            pass

        if status:  
            winreg.SetValueEx(key,APP_NAME,0,winreg.REG_SZ,app_path)
        else:
            try:
                winreg.DeleteValue(key,APP_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)


    def save_settings(self,name_setting,status_setting):
        self.temp_data[name_setting] = status_setting
        with open ('setting_user.json','w',encoding='utf-8') as file:
            json.dump(self.temp_data,file,indent=4,ensure_ascii=False)


if __name__ == "__main__":
    app = App()
    from core.voice_engine import Voice_enginer
    Voice = Voice_enginer()
    app.main_menu()
    app.mainloop()