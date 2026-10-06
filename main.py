import customtkinter as ctk
import winreg
import sys
import json
import voice_engine

ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('dark-blue')

APP_NAME = 'garvis'
REG_PATH = r'Software\Microsoft\Windows\CurrentVersion\Run'

standard_user_setting = {
    'name_user':'',
    'stats_avto_load':0
    }

# Основной интерфейс приложения / interface
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.setting()
        self.geometry('720x480')
        self.button = ctk.CTkCheckBox(master=self, 
                                  text='avto load program',
                                  command=self.avto_load)
        self.button_start = ctk.CTkButton(master=self,
                                          text = 'start',
                                          command=self.start_programm)
        if self.temp_data['stats_avto_load']:
            self.button.select()
        else:
            self.button.deselect()

    #Чтение настроек пользователя/или их создание в противном случае
    def setting(self):
        try:
            with open('setting_user.json','r',encoding='utf-8') as file:
                self.temp_data = json.load(file)

        except FileNotFoundError:
            with open('setting_user.json','w',encoding='utf-8') as file:
                json.dump(standard_user_setting,file,indent=4,ensure_ascii=False)
                self.setting()


    def main_menu(self):
        self.button.place(x=50,y=400-10)
        self.button_start.place(x=450,y=400-10)


    def start_programm(self):
        pass

    
    # Фукция для изменения состояния автозапуска программы / avto load program
    def avto_load(self):
        status = self.button.get()
        self.save_settings('stats_avto_load',status)
        app_path = f'"{sys.executable}" "{__file__}"'
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,REG_PATH,0,winreg.KEY_WRITE)
        
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
    app.setting()
    app.main_menu()
    app.mainloop()