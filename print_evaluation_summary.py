import pandas as pd
import pickle
import torch
from datetime import datetime
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

WIDTH = 60


def section_title(text):
    print(text.center(WIDTH))


def subsection_title(text):
    print(text)


def metric_row(label, value):
    print(f"  {label:<12}: {value:.4f}")



# LOAD VALIDATION DATA
val = pd.read_csv("val_combined.csv")
val["text"] = val["subject"].fillna("") + " " + val["body"].fillna("")
val_labels = val["label"]
label2id = {"legitimate": 0, "phishing": 1}
val_binary = val_labels.map(label2id)


# RANDOM FOREST
with open("rf_pipeline_combined.pkl", "rb") as f:
    rf_pipeline = pickle.load(f)

rf_features = rf_pipeline["vectoriser"].transform(val["text"])
rf_preds = rf_pipeline["model"].predict(rf_features)
rf_preds_binary = pd.Series(rf_preds).map(label2id)

rf_accuracy = accuracy_score(val_binary, rf_preds_binary)
rf_precision = precision_score(val_binary, rf_preds_binary)
rf_recall = recall_score(val_binary, rf_preds_binary)
rf_f1 = f1_score(val_binary, rf_preds_binary)

# DISTILBERT
if torch.backends.mps.is_available():
    device = torch.device("mps")
elif torch.cuda.is_available():
    device = torch.device("cuda")
else:
    device = torch.device("cpu")

tokenizer = DistilBertTokenizer.from_pretrained("distilbert_phishing")
db_model = DistilBertForSequenceClassification.from_pretrained("distilbert_phishing")
db_model.to(device)
db_model.eval()

db_preds = []
batch_size = 16
texts = val["text"].tolist()

with torch.no_grad():
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        encodings = tokenizer(batch, truncation=True, padding="max_length", max_length=128, return_tensors="pt")
        encodings = {k: v.to(device) for k, v in encodings.items()}
        outputs = db_model(**encodings)
        batch_preds = torch.argmax(outputs.logits, dim=1).cpu().tolist()
        db_preds.extend(batch_preds)

db_accuracy = accuracy_score(val_binary, db_preds)
db_precision = precision_score(val_binary, db_preds)
db_recall = recall_score(val_binary, db_preds)
db_f1 = f1_score(val_binary, db_preds)


# PRINT PROFESSIONAL SUMMARY
print()
section_title("PHISHING DETECTION - MODEL EVALUATION SUMMARY")
print(f"  Dataset : val_combined.csv ({len(val)} emails)".ljust(WIDTH))
print(f"  Device  : {device}".ljust(WIDTH))
print()

subsection_title("RANDOM FOREST  (TF-IDF + Random Forest)")
metric_row("Accuracy", rf_accuracy)
metric_row("Precision", rf_precision)
metric_row("Recall", rf_recall)
metric_row("F1 Score", rf_f1)
print()

subsection_title("DISTILBERT  (fine tuned, 3 epochs)")
metric_row("Accuracy", db_accuracy)
metric_row("Precision", db_precision)
metric_row("Recall", db_recall)
metric_row("F1 Score", db_f1)
print()

section_title("SIDE BY SIDE COMPARISON")
print(f"  {'Metric':<12}{'Random Forest':>16}{'DistilBERT':>16}")
print(f"  {'Accuracy':<12}{rf_accuracy:>16.4f}{db_accuracy:>16.4f}")
print(f"  {'Precision':<12}{rf_precision:>16.4f}{db_precision:>16.4f}")
print(f"  {'Recall':<12}{rf_recall:>16.4f}{db_recall:>16.4f}")
print(f"  {'F1 Score':<12}{rf_f1:>16.4f}{db_f1:>16.4f}")
print()