import customtkinter as ctk
import winreg
import sys
import json
import os
import re
import urllib.request
import webbrowser
from pathlib import Path
import sounddevice as sd
import threading

ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('dark-blue')

APP_NAME = 'garvis'
APP_VERSION = "0.0.3"
GITHUB_REPO = "bous-devysek/my_dgarvis"
GITHUB_RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases?per_page=1"
GITHUB_TAGS_API = f"https://api.github.com/repos/{GITHUB_REPO}/tags?per_page=1"
REG_PATH = r'Software\Microsoft\Windows\CurrentVersion\Run'
SETTINGS_PATH = Path(__file__).resolve().parent.parent / "config" /"setting_user.json"

standard_user_setting = {
    "name_asistet":'джарвис',
    "stats_auto_load":0,
    "input_device": None,
    }


def parse_version(text: str) -> tuple[int, int, int]:
    match = re.match(r"v?(\d+)\.(\d+)\.(\d+)", text.strip())
    return tuple(int(part) for part in match.groups()) if match else (0, 0, 0)


def github_json(url: str):
    """Запрос к GitHub API с User-Agent."""
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "garvis-updater",
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.load(response)

#---------------------------------------------------------------
#Интерфейс приложения / interface
#---------------------------------------------------------------

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.setting()
        self.geometry('280x360')
        self.latest_release = None
        self.chek_box = ctk.CTkCheckBox(master=self, 
                                    text='auto load program',
                                    command=self.auto_load)
        self.swith = ctk.CTkSwitch(master=self,
                                    text = 'status',
                                    command=self.stream_start)
        self.entry = ctk.CTkEntry(master=self,
                                    placeholder_text=
                                    "придумайте имя")
        self.name_asisten_laber = ctk.CTkLabel(master=self,
                                    text=f'сейчас: {self.temp_data["name_asistet"]}',
                                    text_color="gray")
        self.button_chek = ctk.CTkButton(master=self,
                                    text="отправить",
                                    command=self.chek_status_entry)
        self.version_label = ctk.CTkLabel(master=self,
                                    text=f"версия {APP_VERSION}",
                                    text_color="gray")
        self.update_button = ctk.CTkButton(master=self,
                                    text="проверить обновления",
                                    command=self.check_updates)
        self.update_status = ctk.CTkLabel(master=self, text="")
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
            self.after(0, lambda e=exc: self.status.configure(text=f"ошибка: {e}"))


    #Чтение настроек пользователя/или их создание в противном случае
    def setting(self):
        try:
            with open(SETTINGS_PATH,'r',encoding='utf-8') as file:
                self.temp_data = json.load(file)

        except FileNotFoundError:
            with open(SETTINGS_PATH,'w',encoding='utf-8') as file:
                json.dump(standard_user_setting,file,indent=4,ensure_ascii=False)
            self.temp_data = standard_user_setting


    def main_menu(self):
        self.chek_box.pack(padx=5,pady=20)
        self.swith.pack(padx=5,pady=20)
        self.entry.pack(padx=5,pady=10)
        self.name_asisten_laber.pack(padx=5,pady=(10,0))
        self.button_chek.pack(padx=5,pady=5)
        self.version_label.pack(padx=5,pady=(15, 0))
        self.update_button.pack(padx=5,pady=5)
        self.update_status.pack(padx=5,pady=(0, 10))


    def chek_status_entry(self):
        name_asistent = self.entry.get()
        if name_asistent != "":
            print(f"Новое имя {name_asistent}")
            name_asistent = name_asistent.lower()
            self.save_settings("name_asistet", name_asistent) 
            self.name_asisten_laber.configure(text=f'сейчас: {self.temp_data["name_asistet"]}')


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

    # ---------------------------------------------------------------- обновления

    def _update_button(self,status_text):
        self.update_button.configure(
                    state="normal",
                    text=status_text,
                    command=self.open_release_page,
                )

        
    def check_updates(self):
        self.update_button.configure(state="disabled", text="проверяю…")
        self.update_status.configure(text="")
        threading.Thread(target=self._check_updates_worker, daemon=True).start()


    def _check_updates_worker(self):
        try:
            releases = github_json(GITHUB_RELEASES_API)
            release = releases[0] if releases else None

            # Если релиз ещё не оформлен на GitHub, смотрим на теги.
            if release is None:
                tags = github_json(GITHUB_TAGS_API)
                if tags:
                    release = {
                        "tag_name": tags[0]["name"],
                        "html_url": f"https://github.com/{GITHUB_REPO}/releases",
                    }

            if release and parse_version(release.get("tag_name", "")) > parse_version(APP_VERSION):
                self.after(0, lambda: self._show_update(release,"скачать обновление"))
            else:
                self.after(0, self._show_latest("проверить обновления"))
        except Exception:
            self.after(0, self._show_update_error("проверить обновления"))

    def _show_update(self, release,text):
        self.latest_release = release
        version = release.get("tag_name", "").lstrip("vV")
        self.update_status.configure(text=f"доступна версия {version}")
        self._update_button(text)


    def _show_latest(self,text):
        self.latest_release = None
        self.update_status.configure(text="у вас последняя версия")
        self._update_button(text)


    def _show_update_error(self,text):
        self.update_status.configure(text="не удалось проверить обновления")
        self._update_button(text)


    def open_release_page(self):
        if self.latest_release:
            webbrowser.open(self.latest_release["html_url"])


if __name__ == "__main__":
    app = App()
    app.main_menu()
    app.mainloop()