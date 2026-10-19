import joblib
import word_processing as wp

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

model_data = joblib.load('voice_model.pkl')

vectorizer = model_data['vectorizer']
clf = model_data['classifier']


def determination_probabilities(user_query):
    print(user_query)
    # получение матрицы из запроса
    matrix = vectorizer.transform([' '.join(user_query)])
    # получение списка вероятностей из матрицы
    list_probabilities = clf.predict_proba(matrix)
    return list_probabilities


def defining_invoking_commands(user_query):
    list_probabilities = determination_probabilities(user_query)
    return None


test = 'открой доту' 
print(test)
print(determination_probabilities(wp.lemmatization(test)))