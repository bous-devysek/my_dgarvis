import os,re,ctypes
import rapidfuzz as rap

ID_STEAM_GAME={
    "дот": "570",
    "факторио": "427520",
    "дедлок": "1422450",
    "metro 2033 redux": "286690",
    "miside": "2527500",
    "no, i'm not a human": "3180070",
    "oneshot": "420530",
    "raft": "648800",
    "rain world": "312520",
    "bloons td 6": "960090",
    "cuphead": "268910",
    "devil may cry hd collection": "631510",
    "doom": "379720",
    "frostpunk": "323190",
    "geometry dash": "322170",
    "hollow knight: silksong": "1030300",
    "phasmophobia": "739630",
    "war thunder": "236390",
    "project zomboid": "108600",
    "rust": "252490",
    "sons of the forest": "1326470",
    "tmodloader": "1281930",
    "detroit: become human": "1222140",
    "doom: the dark ages": "3017860",
    "ultrakill": "1229490",
    "doom eternal": "782330",
    "factorio": "427520",
    "mindustry": "1127400",
    "the coffin of andy and leyley": "2378900",
    "barro f": "1239260",
    "house flipper": "613100",
    "хаус флиппер": "613100",
    "a hat in time": "253230",
    "r.e.p.o.": "3241660",
    "terraria": "105600",
    "carrion": "953490",
    "dorfromantik": "1455840",
    "meccha chameleon": "4704690",
    "payday 2": "218620",
    "the forest": "242760",
    "ark: survival evolved": "346110",
    "barro t23": "2379030",
    "deadlock": "1422450",
    "don't starve together": "322330",
    "euro truck simulator 2": "227300",
    "fortify": "505040",
    "garry's mod": "4000",
    "megabonk": "3405340",
    "sandbox": "2438020",
    "slime rancher": "433340",
    "the farmer was replaced": "2060160",
    "undertale": "391540",
    "cult of the lamb": "1313140",
    "hollow knight": "367520",
    "left 4 dead 2": "550",
    "marvel's spider-man remastered": "1817070",
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


def _normalize(text: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", "", text.lower()).split())


def system_command():
    pass


def music_command(user_query: str) -> None:
    pass


_STEAM_BY_NORM = {_normalize(name): name for name in ID_STEAM_GAME}

_TRIGGERS = {"открой", "открыть", "запусти", "запустить", "включи", "включить",
             "вруби", "врубить", "загрузи", "загрузить", "поиграть", "игра",
             "пожалуйста","игру"}

def dispatch(user_query: str) -> None:
    query = _normalize(user_query)

    print(f'текущий запрос: {query}')
    for phrase in sorted(WORD_ACTIONS, key=lambda key: len(_normalize(key)), reverse=True):
        normalized_phrase = _normalize(phrase)
        if not normalized_phrase:
            continue
        if not re.search(rf"(?<!\w){re.escape(normalized_phrase)}(?!\w)", query):
            continue
        kind, argument = WORD_ACTIONS[phrase]
        print(f'результат{kind}: {argument}')
        print("---------------")
        if kind == "browser":
            open_browser(argument)
            return
        if kind == "music":
            play_or_pause_music()
            return
        if kind == "game":
            open_steam_game(argument)
            return

    query = " ".join(word for word in query.split() if word not in _TRIGGERS)
    if not query:
        print("не понял, какую игру открыть")
        return

    matches = rap.process.extract(query, _STEAM_BY_NORM.keys(),
                                  scorer=rap.fuzz.WRatio, limit=2)
    name, score, _ = matches[0]
    runner_up = matches[1][1] if len(matches) > 1 else 0
    print(f'лучший вариант: {name} ({score:.0f}), второй: {runner_up:.0f}')

    if score < 80:                      # мусор не запускаем
        print("игра не распознана")
        return
    if score - runner_up < 8:
        print(f'не уверен: {name} ({score:.0f}) или {matches[1][0]} ({runner_up:.0f})')
        return

    print(f'результат {_STEAM_BY_NORM[name]}')
    print("---------------")
    open_steam_game(_STEAM_BY_NORM[name])


COMMAND_REGISTRY = {
    "run_application": dispatch,
    "system_commands": (lambda query : print('не реализовано')),                      
}

WORD_ACTIONS = {
    **{name: ("game", name) for name in ID_STEAM_GAME},
    **{name: ("browser", name) for name in BROWSER_URLS},
    **{name:("music", name) for name in MUSIC_OBJECTS},
}