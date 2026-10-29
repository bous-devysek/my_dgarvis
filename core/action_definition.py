from rapidfuzz import fuzz,process
from dataclasses import dataclass
from pathlib import Path
import core.word_processing as wp
import re,json,os,ctypes


_TRIGGER_RUN_APPLICATION = frozenset({
    "открыть", "открывать", "запустить", "запускать",
    "включить", "включать", "врубить", "врубать",
    "загрузить", "загружать", "поиграть", "играть",
    "открою",
})

_INTENTS = {
    "run_application": _TRIGGER_RUN_APPLICATION,
    #"close_application":_TRIGER_CLOSE_APPLICATION,
}

HANDLERS = {
    "game": lambda e: os.startfile(f"steam://run/{e.value}"),
    "browser": lambda e: os.startfile(e.value),
    "music": lambda e: play_or_pause_music(),
}

VK_MEDIA_PLAY_PAUSE = 0xB3 # Virtual Key 
VK_MEDIA_SKIP = 0xB0 
KEYEVENTF_KEYUP = 0x0002

def play_or_pause_music() -> None:
    user32 = ctypes.windll.user32
    user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
    user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, KEYEVENTF_KEYUP, 0) 

def _normalize(text: str) -> str:
    text = text.lower().replace("ё","е")
    return " ".join(re.sub(r"[^\w\s]", "", text).split())


def _same_polarity(a: str, b: str) -> bool:
    return a.startswith("вы") == b.startswith("вы")


def strip_triggers(text: str) -> str:
    words = _normalize(text).split()
    return " ".join(w for w in words if w not in _TRIGGER_RUN_APPLICATION)

#------------------------Данные---------------------------------
DATA_PATH = Path(__file__).resolve().parent.parent /"data"/"entities.json"
with open(DATA_PATH,encoding="utf-8-sig") as file:
    DATA = json.load(file)
#---------------------------------------------------------------

#---------------------Создание-модели-данных--------------------
@dataclass(frozen=True)
class Entity:
    canonical:str
    kind:str
    value:str
    aliases:tuple[str,...] = ()


#Загрузка данных
def load() -> list[Entity]:
    entities = []
    for item in DATA:
        entities.append(Entity(item["canonical"],
                            item["kind"],
                            item["value"],
                            tuple(item["aliases"])))
    return entities


class Vocabulary:
    def __init__(self, entities):
        self.entities = list(entities)
        self._by_key: dict[str, Entity] = {}

        for e in self.entities:
            for name in (e.canonical, *e.aliases):   # ключ — и канон, и алиасы
                key = _normalize(name)
                if key in self._by_key and self._by_key[key] != e:
                    raise ValueError(f"коллизия ключа {key!r}")
                self._by_key[key] = e

    def get(self, name: str) -> Entity | None:
        """Точный поиск по названию или алиасу."""
        return self._by_key.get(_normalize(name))

    def of_kind(self, kind: str) -> list[Entity]:
        return [e for e in self.entities if e.kind == kind]

    def resolve(self, text: str, threshold=80, margin=8):
        query = _normalize(text)

        exact = self._by_key.get(query)
        if exact:
            return exact, 100.0, 100.0

        found = process.extract(query, self._by_key.keys(), scorer=fuzz.WRatio, limit=5)

        seen, ranked = set(), []
        for key, score, _ in found:
            e = self._by_key[key]
            if e.canonical in seen:      # алиасы одной сущности не занимают два места
                continue
            seen.add(e.canonical)
            ranked.append((e, score))

        if not ranked or ranked[0][1] < threshold:
            return None
        runner = ranked[1][1] if len(ranked) > 1 else 0.0
        if ranked[0][1] - runner < margin:
            return None
        return ranked[0][0], ranked[0][1], runner

VOCAB = Vocabulary(load())
#----------------------------------------------------------------

#---------------------Обработка-команд--------------------------
def detect_intent(user_query: str) -> str|None:
    print("------Обработка-команды------")
    query = _normalize(user_query)
    print(f'Текущий запрос {query}')
    words = set(query.split())
    #Cлово есть в тригер словах
    for intent, triggers in _INTENTS.items():
        if words & triggers:
            print(f"Интент: {intent}")
            return intent
    #Слова нет или оно искаверкано
    else:
        best = None
        for word in words:
            if len(word) < 3:
                continue
            minscore = 90 if len((word)) <= 4 else 80
            for intent, triggers in _INTENTS.items():
                for trigger in triggers:
                    if not _same_polarity(word,trigger):
                        continue
                    score = fuzz.WRatio(word,trigger)
                    if score >= minscore and (best is None or score > best[1]):
                        best = (intent,score,trigger)
        if best:
            intent,score,trigger = best
            print(f"Интент: {intent}")
            return intent
    with open("misunderstood intents","a",encoding="utf-8") as file:
        file.write(query)
    print(f"По запросу {query} не распознано ни 1 интета")

def command_processing(user_query:str) -> None:
    user_query = " ".join(wp.lemmatization(user_query))
    command = detect_intent(user_query)
    if command != "run_application":
        print("команда не распознана")
        return

    match = VOCAB.resolve(strip_triggers(user_query))          # resolve из прошлого обсуждения
    if match is None:
        with open("misunderstood_request","a",encoding="utf-8") as file:
            file.write(user_query)
        print("не понял, что открыть")
        return

    entity, score, runner = match
    HANDLERS[entity.kind](entity)
#---------------------------------------------------------------