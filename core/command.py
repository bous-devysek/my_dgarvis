import os
import queue

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
    "гитхаб":"https://github.com/"
}

def open_steam_game(argument: str) -> None:
    os.startfile(f'steam://run/{ID_STEAM_GAME[argument]}')


def open_browser(argument: str) -> None:
    os.startfile(BROWSER_URLS[argument])


def call_command(user_command,user_query):
    COMMAND_REGISTRY[user_command](user_query)


# -------------------Реестр---------------------
COMMAND_REGISTRY = {

    "run_application": (run_application := lambda query: dispatch(query)),
    "system_command": (lambda query : print('не реализовано'))
                        
}

WORD_ACTIONS = {
    **{name: ("game", name) for name in ID_STEAM_GAME},
    **{name: ("browser", name) for name in BROWSER_URLS},
}

def dispatch(user_query: str) -> None:
    for word in user_query.split():
        action = WORD_ACTIONS.get(word)
        if action is None:
            continue
        kind, argument = action
        if kind == "game":
            open_steam_game(argument)
        elif kind == "browser":
            open_browser(argument)
        return  
    print("ничего не распознано в запросе")


def system_command():
    pass

