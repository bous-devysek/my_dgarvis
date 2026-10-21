import os

ID_STEAM_GAME={
    "дот": "570",
    "факторио": "427520",
    "дедлок": "1422450"
}

LIST_NAME_GAME=[
    "дот","факторио","дедлок"
]

BRAUSER_NAME=[
    "фаерфокс","хром","браузер","интернет"
]

def open_steam_game(argument):
    os.startfile(f'steam://run/{ID_STEAM_GAME[argument]}')

# определение принадлежности программы и её запуск
def run_application(user_query):
    #проверка каждого слова на принадлежность
    for name in user_query.split():
        if name in LIST_NAME_GAME:
            name_command = name
            open_steam_game(name_command)
            break

        elif name in BRAUSER_NAME:
            os.startfile("https://")


def system_command():
    pass

