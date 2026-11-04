import customtkinter as ctk
import winreg
import sys
import json
import os
from pathlib import Path
import sounddevice as sd
import threading

ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('dark-blue')

APP_NAME = 'garvis'
REG_PATH = r'Software\Microsoft\Windows\CurrentVersion\Run'
SETTINGS_PATH = Path(__file__).resolve().parent / "setting_user.json"

standard_user_setting = {
    "name_asistet":'джарвис',
    "stats_auto_load":0,
    "input_device": None,
    }

#---------------------------------------------------------------
#Интерфейс приложения / interface
#---------------------------------------------------------------

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.setting()
        self.geometry('250x250')
        self.chek_box = ctk.CTkCheckBox(master=self, 
                                text='auto load program',
                                command=self.auto_load)
        self.swith = ctk.CTkSwitch(master=self,
                                        text = 'status',
                                        command=self.stream_start)
        self.entry = ctk.CTkEntry(master=self,
                                    placeholder_text=
                                    "придумайте имя")
        self.button_chek = ctk.CTkButton(master=self,
                                    text="отправить",
                                    command=self.chek_status_entry)
        if self.temp_data['stats_auto_load']:
            self.chek_box.select()
        else:
            self.chek_box.deselect()

        if not self.temp_data["input_device"]:
            input_device,_ = sd.default.device 
            self.save_settings("input_device",input_device)

        self.voice = None
        self.status = ctk.CTkLabel(self, text="загружаю модель…")
        self.status.pack()
        threading.Thread(target=self._load_voice, daemon=True).start()

    def _load_voice(self):
        from core.voice_engine import Voice_enginer
        try:
            self.voice = Voice_enginer()
            self.after(0, lambda: self.status.configure(text="готов"))
        except Exception as exc:
            self.after(0, lambda: self.status.configure(text=f"ошибка: {exc}"))


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
        self.chek_box.pack(padx=5,pady=20)
        self.swith.pack(padx=5,pady=20)
        self.entry.pack(padx=5,pady=10)
        self.button_chek.pack(padx=5,pady=5)


    def chek_status_entry(self):
        name_asistent = self.entry.get()
        if name_asistent != "":
            print(f"Новое имя {name_asistent}")
            name_asistent = name_asistent.lower()
            self.save_settings("name_asistet", name_asistent) 


    #функция отвечающая за запись голоса
    def stream_start(self):
        self.status_asistent = self.swith.get()
        self.voice.voise_assistent(self.status_asistent)


    # Фукция для изменения состояния автозапуска программы / avto load program
    def auto_load(self):
        print('статус auto-load изменен')
        status = self.chek_box.get()
        self.save_settings('stats_auto_load',status)
        app_path = f'"{sys.executable}" "{Path(__file__).resolve()}"'
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
        with open (SETTINGS_PATH,'w',encoding='utf-8') as file:
            json.dump(self.temp_data,file,indent=4,ensure_ascii=False)


if __name__ == "__main__":
    app = App()
    app.main_menu()
    app.mainloop()