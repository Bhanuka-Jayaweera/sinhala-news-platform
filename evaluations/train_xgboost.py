"""
Train the "light" (TF-IDF + XGBoost) classification route and export the
artifacts to the exact paths news_app/services/classifier.py loads at
runtime:
    temp/models/xgboost/xgbclassifier.json   (native XGBoost format)
    temp/models/xgboost/tfidf_vectorizer.pkl (pickle)

Run from the repo root:
    python evaluations/train_xgboost.py
"""
import pickle
import sys
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
import xgboost as xgb

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from news_app.constants.class_label_mapper import ID_TO_LABEL  # noqa: E402

DATASET_PATH = REPO_ROOT / "evaluations" / "dataset" / "upgraded-sinhala-news-categories.csv"
MODEL_OUT = REPO_ROOT / "temp" / "models" / "xgboost" / "xgbclassifier.json"
VECTORIZER_OUT = REPO_ROOT / "temp" / "models" / "xgboost" / "tfidf_vectorizer.pkl"


def main():
    df = pd.read_csv(DATASET_PATH)
    X, y = df["comments"], df["labels"]

    unexpected_labels = set(y.unique()) - set(ID_TO_LABEL.keys())
    if unexpected_labels:
        raise ValueError(
            f"Dataset has label ids not present in ID_TO_LABEL: {unexpected_labels}"
        )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    vectorizer = TfidfVectorizer(max_features=5000)
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)

    model = xgb.XGBClassifier(tree_method="hist")
    model.fit(X_train_tfidf, y_train)

    y_pred = model.predict(X_test_tfidf)

    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="weighted")

    print(f"Accuracy: {accuracy:.4f}")
    print(f"Weighted F1: {f1:.4f}")
    print()

    labels_present = sorted(y.unique())
    target_names = [ID_TO_LABEL[label_id] for label_id in labels_present]
    print(
        classification_report(
            y_test, y_pred, labels=labels_present, target_names=target_names, zero_division=0
        )
    )

    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(str(MODEL_OUT))
    with open(VECTORIZER_OUT, "wb") as f:
        pickle.dump(vectorizer, f)

    print(f"Saved model to: {MODEL_OUT}")
    print(f"Saved vectorizer to: {VECTORIZER_OUT}")


if __name__ == "__main__":
    main()
