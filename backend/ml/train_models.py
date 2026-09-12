import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_absolute_error

from generate_synthetic_data import make_category_dataset, make_priority_dataset

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODEL_DIR, exist_ok=True)


def train_category_model():
    df = make_category_dataset(n_per_class=150)
    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["category"], test_size=0.2, random_state=42, stratify=df["category"]
    )
    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
        ("clf", LogisticRegression(max_iter=1000)),
    ])
    pipe.fit(X_train, y_train)
    acc = accuracy_score(y_test, pipe.predict(X_test))
    print(f"[category model] test accuracy: {acc:.3f}")
    joblib.dump(pipe, os.path.join(MODEL_DIR, "category_model.joblib"))


def train_priority_model():
    df = make_priority_dataset(n=1500)
    X = df[["urgency", "frequency", "days_open"]]
    y = df["priority_score"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=200, max_depth=6, random_state=42)
    model.fit(X_train, y_train)
    mae = mean_absolute_error(y_test, model.predict(X_test))
    print(f"[priority model] test MAE: {mae:.2f} / 100")
    print(f"[priority model] feature importances: "
          f"urgency={model.feature_importances_[0]:.2f}, "
          f"frequency={model.feature_importances_[1]:.2f}, "
          f"days_open={model.feature_importances_[2]:.2f}")
    joblib.dump(model, os.path.join(MODEL_DIR, "priority_model.joblib"))


def train_dedup_vectorizer():
    """
    Fit a TF-IDF vectorizer over a broad vocabulary of complaint-style text
    so the dedup module has a stable vector space (acts as our lightweight,
    fully-offline stand-in for a hosted embeddings API / vector DB).
    """
    df = make_category_dataset(n_per_class=150)
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
    vec.fit(df["text"])
    joblib.dump(vec, os.path.join(MODEL_DIR, "dedup_vectorizer.joblib"))
    print("[dedup vectorizer] fitted and saved")


if __name__ == "__main__":
    train_category_model()
    train_priority_model()
    train_dedup_vectorizer()
    print("All models trained and saved to", MODEL_DIR)

