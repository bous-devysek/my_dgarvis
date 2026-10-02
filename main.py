import customtkinter as ctk


ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('dark-blue')

# Фукция для изменения состояния автозапуска программы / avto load program
def avto_load():
    pass
    #status = button.get()

# Основной интерфейс приложения / interface
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry('720x480')
        self.button = ctk.CTkCheckBox(master=self, 
                                  text='avto load program',
                                  command=avto_load)


    def main_menu(self):
        self.button.place(x=360,y=240)
        

        

if __name__ == "__main__":
    app = App()
    app.main_menu()
    app.mainloop()