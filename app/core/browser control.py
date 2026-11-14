import asyncio
from playwright.async_api import async_playwright
import winreg
import re 

def get_default_windows_browser():
    try:
        root = winreg.HKEY_CURRENT_USER
        path = f'Software\\Microsoft\\Windows\\Shell\\Associations\\UrlAssociations\\http\\UserChoice'
        with winreg.OpenKey(root,path,0,winreg.KEY_READ) as key:
            prog_id,_ = winreg.QueryValueEx(key, "ProgId")
            
        command_path = f"{prog_id}\\shell\\open\\command"
        with winreg.OpenKey(
            winreg.HKEY_CLASSES_ROOT, command_path, 0, winreg.KEY_READ
        ) as key:
            raw_command, _ = winreg.QueryValueEx(key, "")

        match = re.search(r'([A-Za-z]:\\[^:]+\.exe)', raw_command, re.IGNORECASE)
        if match:
            return match.group(1).strip('"')
        
        
        if ".exe" in raw_command.lower():
            exe_index = raw_command.lower().find(".exe") + 4
            return raw_command[:exe_index].strip('" ')
            
        return raw_command.split()[0].strip('"')

    except FileNotFoundError:
        print("Не удалось найти настройки браузера по умолчанию в реестре.")
        return None
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")
        return None

async def main():
    path_browser = get_default_windows_browser()
    
asyncio.run(main())