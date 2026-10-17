import pymorphy3
# from sklearn.ensemble import 
morph = pymorphy3.MorphAnalyzer()

# функция чистит текст от не букв
def text_clear(input_text):
    input_text = input_text.strip()
    output_text = ''
    for i in input_text:
        if i == ' ' or i.isalpha():
            output_text += i
    return output_text


# Разделение текста на  список слов
def request_filtering(input_text):
    input_text = input_text.lower()
    text = text_clear(input_text)
    list_words = text.split()
    print(list_words)
    return list_words


# Приведение слов в начальную фому
def lemmatization(text):
    list_words = request_filtering(text)
    result = [morph.parse(word)[0].normal_form 
              for word in list_words]
    return result

