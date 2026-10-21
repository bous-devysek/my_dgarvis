import joblib
import core.word_processing as wp
import core.command as command

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

model_data = joblib.load('voice_model.pkl')

vectorizer = model_data['vectorizer']
clf = model_data['classifier']


COMMAND_REGISTRY = {
    "run_application": command.run_application ,
    "system_commands": command.system_command
}

list_command = [
    "run_application",
    "system_commands"
]

def determination_probabilities(user_query):
    copy_user_query = user_query
    print(user_query)
    # получение матрицы из запроса
    matrix = vectorizer.transform([' '.join(user_query)])
    # получение списка вероятностей из матрицы
    list_probabilities = clf.predict_proba(matrix)
    return list_probabilities , copy_user_query

# распознание команд
def defining_invoking_commands(user_query):
    
    # определения списка вероятностей 
    list_probabilities = determination_probabilities(
        wp.lemmatization(user_query))

    # если вероятность каманды больше 70 то выполнить
    if max(list_command) > 70:
        id_max_element = list_probabilities.index(max(list_probabilities))
        user_command = list_command[id_max_element]
        COMMAND_REGISTRY[user_command(user_query)]