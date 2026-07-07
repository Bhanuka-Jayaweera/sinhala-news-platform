"""
Fine-tune the sinbert-1810 checkpoint (currently an MLM checkpoint with no
category head) into a real 14-class sequence classifier.

Saves the fine-tuned checkpoint to a NEW directory
(temp/models/sinbert-1810-categories-finetuned/) and leaves the original
sinbert-1810 checkpoint untouched. classifier.py must be repointed at the
new directory afterwards (see PATH_B_NEXT_STEPS.txt printed at the end).

Run from the repo root:
    python evaluations/train_sinbert.py
    python evaluations/train_sinbert.py --max-samples 1500 --epochs 2   # quick smoke test
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from news_app.constants.class_label_mapper import ID_TO_LABEL, LABEL_TO_ID  # noqa: E402

DATASET_PATH = REPO_ROOT / "evaluations" / "dataset" / "upgraded-sinhala-news-categories.csv"
BASE_CHECKPOINT = REPO_ROOT / "temp" / "models" / "sinbert-1810"
OUTPUT_DIR = REPO_ROOT / "temp" / "models" / "sinbert-1810-categories-finetuned"

# Mirrors classifier.py's content_max_length truncation so train/inference
# preprocessing stays symmetric.
CONTENT_MAX_CHARS = 500
MAX_TOKEN_LENGTH = 256


class NewsDataset(Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        item = {k: v[idx] for k, v in self.encodings.items()}
        item["labels"] = self.labels[idx]
        return item


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return {
        "accuracy": accuracy_score(labels, preds),
        "f1_weighted": f1_score(labels, preds, average="weighted"),
    }


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-samples", type=int, default=None,
                         help="Randomly subsample the dataset to this size (smoke test).")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--output-dir", type=str, default=None,
                         help="Defaults to temp/models/sinbert-1810-categories-finetuned, "
                              "or that name + '-smoketest' when --max-samples is set.")
    return parser.parse_args()


def main():
    args = parse_args()

    df = pd.read_csv(DATASET_PATH)
    df["comments"] = df["comments"].astype(str).str.slice(0, CONTENT_MAX_CHARS)

    unexpected_labels = set(df["labels"].unique()) - set(ID_TO_LABEL.keys())
    if unexpected_labels:
        raise ValueError(f"Dataset has label ids not in ID_TO_LABEL: {unexpected_labels}")

    is_smoke_test = args.max_samples is not None
    if is_smoke_test:
        df = df.sample(n=min(args.max_samples, len(df)), random_state=42)

    if args.output_dir:
        output_dir = Path(args.output_dir)
    elif is_smoke_test:
        output_dir = OUTPUT_DIR.parent / (OUTPUT_DIR.name + "-smoketest")
    else:
        output_dir = OUTPUT_DIR

    # Rare classes can drop to <2 members after subsampling, which breaks
    # stratify -- only stratify on the full dataset.
    stratify = None if is_smoke_test else df["labels"]
    X_train, X_val, y_train, y_val = train_test_split(
        df["comments"], df["labels"], test_size=0.2, random_state=42, stratify=stratify
    )

    tokenizer = AutoTokenizer.from_pretrained(str(BASE_CHECKPOINT))
    model = AutoModelForSequenceClassification.from_pretrained(
        str(BASE_CHECKPOINT),
        num_labels=len(ID_TO_LABEL),
        id2label={i: label for i, label in ID_TO_LABEL.items()},
        label2id=LABEL_TO_ID,
    )

    def tokenize(texts):
        return tokenizer(
            list(texts), truncation=True, max_length=MAX_TOKEN_LENGTH, padding=False
        )

    train_encodings = tokenize(X_train)
    val_encodings = tokenize(X_val)

    train_dataset = NewsDataset(train_encodings, y_train.tolist())
    val_dataset = NewsDataset(val_encodings, y_val.tolist())

    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    training_args = TrainingArguments(
        output_dir=str(REPO_ROOT / "temp" / "sinbert_training_checkpoints"),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=16,
        learning_rate=2e-5,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=1,
        load_best_model_at_end=True,
        metric_for_best_model="f1_weighted",
        logging_steps=50,
        report_to=[],
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    trainer.train()

    metrics = trainer.evaluate()
    print("Final eval metrics:", metrics)

    output_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))
    print(f"Saved fine-tuned model to: {output_dir}")


if __name__ == "__main__":
    main()
