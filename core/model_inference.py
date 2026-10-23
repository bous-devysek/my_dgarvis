import joblib
import core.word_processing as wp
import core.command as command
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

model_data = joblib.load('voice_model.pkl')

vectorizer = model_data['vectorizer']
clf = model_data['classifier']

list_command = [
    "run_application",
    "system_command"
    ]

def determination_probabilities(user_query):
    # получение матрицы из запроса
    matrix = vectorizer.transform([' '.join(user_query)])
    # получение списка вероятностей из матрицы
    list_probabilities = clf.predict_proba(matrix)
    return list_probabilities

# распознание команд
def defining_invoking_commands(user_query):
    print('команда пришла')
    lemmatiz_query = wp.lemmatization(user_query)
    # определения списка вероятностей 
    list_probabilities = determination_probabilities(lemmatiz_query)
    proda = list_probabilities[0]
    # если вероятность каманды больше 70 то выполнить
    id_max = int(proda.argmax())
    if proda[id_max] > 0.7:
        user_command = list_command[id_max]
        print(f'{user_command} {user_query}')
        command.call_command(user_command,' '.join(lemmatiz_query))
    else:
        print('команда не распознана')