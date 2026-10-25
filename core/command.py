import os
import ctypes

ID_STEAM_GAME={
    "дот": "570",
    "факторио": "427520",
    "дедлок": "1422450",
    
}

BROWSER_URLS={
    "фаерфокс":"https://www.google.com",
    "хром":"https://www.google.com",
    "браузер":"https://www.google.com",
    "интернет":"https://www.google.com",
    "youtube":"https://www.youtube.com",
    "ютуб":"https://www.youtube.com",
    "ютуба":"https://www.youtube.com",
    "гитхаб":"https://github.com/",
    "github":"https://github.com/",
    "roblox":"https://www.roblox.com/home"
}

MUSIC_OBJECTS = {
    "трек", "песня", "музыка", "плейлист", "волна", "альбом"
    }

def open_steam_game(argument: str) -> None:
    os.startfile(f'steam://run/{ID_STEAM_GAME[argument]}')


def open_browser(argument: str) -> None:
    os.startfile(BROWSER_URLS[argument])


VK_MEDIA_PLAY_PAUSE = 0xB3 # Virtual Key 
VK_MEDIA_SKIP = 0xB0 
KEYEVENTF_KEYUP = 0x0002

def play_or_pause_music() -> None:
    user32 = ctypes.windll.user32
    user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
    user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, KEYEVENTF_KEYUP, 0) 


# -------------------Реестр---------------------
def call_command(user_command,user_query):
    print(f"--- ОТЛАДКА ---")
    print(f"Принятая команда: '{user_command}'")
    print(f"Принятый запрос: '{user_query}'")
    print(f"Тип запроса: {type(user_query)}")
    print(f"---------------")
    
    if user_command in COMMAND_REGISTRY:
        COMMAND_REGISTRY[user_command](user_query)
    else:
        print(f"Ошибка: Команды '{user_command}' нет в реестре!")


def dispatch(user_query: str) -> None:
    for word in user_query.split():
        print(f'проверяемое слово {word}')
        action = WORD_ACTIONS.get(word)
        print(f'результат{action}')
        print("---------------")
        if action is None:
            continue
        kind, argument = action
        if kind == "game":
            open_steam_game(argument)
        elif kind == "browser":
            open_browser(argument)
        elif kind == "music":
            play_or_pause_music()
        return  
    print("ничего не распознано в запросе")


def system_command():
    pass


def music_command(user_query: str) -> None:
    pass


COMMAND_REGISTRY = {
    "run_application": dispatch,
    "system_commands": (lambda query : print('не реализовано')),                      
}

WORD_ACTIONS = {
    **{name: ("game", name) for name in ID_STEAM_GAME},
    **{name: ("browser", name) for name in BROWSER_URLS},
    **{name:("music", name) for name in MUSIC_OBJECTS},
}

