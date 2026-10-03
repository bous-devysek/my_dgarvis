import customtkinter as ctk
import winreg
import sys

ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('dark-blue')

APP_NAME = 'garvis'
REG_PATH = r'Software\Microsoft\Windows\CurrentVersion\Run'

# Основной интерфейс приложения / interface
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry('720x480')
        self.button = ctk.CTkCheckBox(master=self, 
                                  text='avto load program',
                                  command=self.avto_load)


    def main_menu(self):
        self.button.place(x=360,y=240)

    
    # Фукция для изменения состояния автозапуска программы / avto load program
    def avto_load(self):
        status = self.button.get()
        app_path = f'"{sys.executable}""__file__"'
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,REG_PATH,0,winreg.KEY_WRITE)
        
        if status:  
            winreg.SetValueEx(key,APP_NAME,0,winreg.REG_SZ,app_path)
        else:
            try:
                winreg.DeleteValue(key,APP_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)



        

if __name__ == "__main__":
    app = App()
    app.main_menu()
    app.mainloop()