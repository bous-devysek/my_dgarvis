import customtkinter as tk


tk.set_appearance_mode('dark')
tk.set_default_color_theme('dark-blue')

class App(tk.CTk):
    def __init__(self):
        super().__init__()


        self.geometry('720x480')

        

if __name__ == "__main__":
    app = App()
    app.mainloop()