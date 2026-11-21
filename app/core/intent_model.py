# Получает данные из data/intent.jsonl
# превращает в вектор char-ngram поверх - LogisticRegression или LinearSVC
# потом модель выдает вероятности по интернам

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import joblib ,json
from pathlib import Path
def train(rows, out="data/intent_model.joblib"):
    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)),
        ("clf", LogisticRegression(max_iter=1000, C=4.0)),
    ])
    pipe.fit([r["text"] for r in rows], [r["intent"] for r in rows])
    joblib.dump(pipe, out)
    return pipe


if __name__ == "__main__":
    path = Path(__file__).resolve().parent.parent.parent /"data"/"intents.jsonl"
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    train(rows)