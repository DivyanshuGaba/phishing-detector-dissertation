import pandas as pd
import numpy as np
import pickle
import torch
import matplotlib.pyplot as plt
import seaborn as sns
import os
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, roc_curve, auc, precision_recall_curve
)
import time

# Create output folder for plots
os.makedirs("plots", exist_ok=True)

# Device setup
if torch.backends.mps.is_available():
    device = torch.device("mps")
    print("Using Apple Silicon MPS")
else:
    device = torch.device("cpu")
    print("Using CPU")

# Load test set
print("\nLoading test set...")
test = pd.read_csv("test_combined.csv")
test["text"] = test["subject"].fillna("") + " " + test["body"].fillna("")
print(f"Test emails: {len(test)}")
print(f"Label distribution:\n{test['label'].value_counts()}")


# RANDOM FOREST EVALUATION

print("\nRANDOM FOREST EVALUATION")

# Load RF model
with open("rf_pipeline_combined.pkl", "rb") as f:
    rf_pipeline = pickle.load(f)

vectoriser = rf_pipeline["vectoriser"]
rf_model = rf_pipeline["model"]

# Transform test features
test_features = vectoriser.transform(test["text"])
test_labels = test["label"]

# RF Latency measurement
print("\nMeasuring RF inference latency...")
latency_runs = []
sample_feature = test_features[0]
for _ in range(10):
    start = time.perf_counter()
    rf_model.predict(sample_feature)
    end = time.perf_counter()
    latency_runs.append((end - start) * 1000)
rf_latency = np.mean(latency_runs)
print(f"RF average latency: {rf_latency:.4f} ms per email")

# RF Predictions
rf_preds = rf_model.predict(test_features)
rf_proba = rf_model.predict_proba(test_features)[:, 1]

# Convert labels to binary
label2id = {"legitimate": 0, "phishing": 1}
test_binary = test_labels.map(label2id)
rf_preds_binary = pd.Series(rf_preds).map(label2id)

# RF Metrics
rf_accuracy  = accuracy_score(test_binary, rf_preds_binary)
rf_precision = precision_score(test_binary, rf_preds_binary)
rf_recall    = recall_score(test_binary, rf_preds_binary)
rf_f1        = f1_score(test_binary, rf_preds_binary)
rf_cm        = confusion_matrix(test_binary, rf_preds_binary)

print(f"\nRandom Forest Test Results:")
print(f"Accuracy:  {rf_accuracy:.4f}")
print(f"Precision: {rf_precision:.4f}")
print(f"Recall:    {rf_recall:.4f}")
print(f"F1 Score:  {rf_f1:.4f}")
print(f"Latency:   {rf_latency:.4f} ms per email")

# RF ROC
rf_fpr, rf_tpr, _ = roc_curve(test_binary, rf_proba)
rf_auc = auc(rf_fpr, rf_tpr)
print(f"AUC:       {rf_auc:.4f}")

# RF Confusion Matrix Plot
plt.figure(figsize=(6, 5))
sns.heatmap(rf_cm, annot=True, fmt="d", cmap="Blues",
            xticklabels=["Legitimate", "Phishing"],
            yticklabels=["Legitimate", "Phishing"])
plt.title("Random Forest - Confusion Matrix (Test Set)")
plt.ylabel("Actual")
plt.xlabel("Predicted")
plt.tight_layout()
plt.savefig("plots/rf_confusion_matrix.png", dpi=150)
plt.close()
print("Saved: plots/rf_confusion_matrix.png")

# RF Feature Importance Plot
feature_names = vectoriser.get_feature_names_out()
importances = rf_model.feature_importances_
top_indices = np.argsort(importances)[::-1][:20]
top_features = [feature_names[i] for i in top_indices]
top_importances = [importances[i] for i in top_indices]

plt.figure(figsize=(10, 6))
sns.barplot(x=top_importances, y=top_features, hue=top_features,
            palette="Blues_r", legend=False)
plt.title("Random Forest - Top 20 Feature Importances (Gini)")
plt.xlabel("Importance Score")
plt.ylabel("Feature")
plt.tight_layout()
plt.savefig("plots/rf_feature_importance.png", dpi=150)
plt.close()
print("Saved: plots/rf_feature_importance.png")


# DISTILBERT EVALUATION
print("\nDISTILBERT EVALUATION")

# Load DistilBERT
print("\nLoading DistilBERT model...")
tokeniser = DistilBertTokenizer.from_pretrained("distilbert_phishing")
db_model = DistilBertForSequenceClassification.from_pretrained("distilbert_phishing")
db_model = db_model.to(device)
db_model.eval()

# Dataset class
class EmailDataset(Dataset):
    def __init__(self, texts, labels, tokeniser, max_length=128):
        self.texts = texts
        self.labels = labels
        self.tokeniser = tokeniser
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        encoding = self.tokeniser(
            str(self.texts[idx]),
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt"
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
            "label": torch.tensor(self.labels[idx], dtype=torch.long)
        }

test_dataset = EmailDataset(
    test["text"].tolist(),
    test_binary.tolist(),
    tokeniser
)
test_loader = DataLoader(test_dataset, batch_size=8, shuffle=False)

# DistilBERT Latency
print("\nMeasuring DistilBERT inference latency...")
sample_text = str(test["text"].iloc[0])
sample_enc = tokeniser(
    sample_text, truncation=True, padding="max_length",
    max_length=128, return_tensors="pt"
)
sample_ids = sample_enc["input_ids"].to(device)
sample_mask = sample_enc["attention_mask"].to(device)

latency_runs = []
with torch.no_grad():
    for _ in range(10):
        start = time.perf_counter()
        db_model(input_ids=sample_ids, attention_mask=sample_mask)
        end = time.perf_counter()
        latency_runs.append((end - start) * 1000)
db_latency = np.mean(latency_runs)
print(f"DistilBERT average latency: {db_latency:.4f} ms per email")

# DistilBERT Predictions
print("\nRunning DistilBERT on test set...")
db_preds = []
db_proba = []
db_labels = []

with torch.no_grad():
    for batch in test_loader:
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["label"]

        outputs = db_model(input_ids=input_ids, attention_mask=attention_mask)
        probs = torch.softmax(outputs.logits, dim=1)[:, 1]
        preds = torch.argmax(outputs.logits, dim=1)

        db_preds.extend(preds.cpu().numpy())
        db_proba.extend(probs.cpu().numpy())
        db_labels.extend(labels.numpy())

# DistilBERT Metrics
db_accuracy  = accuracy_score(db_labels, db_preds)
db_precision = precision_score(db_labels, db_preds)
db_recall    = recall_score(db_labels, db_preds)
db_f1        = f1_score(db_labels, db_preds)
db_cm        = confusion_matrix(db_labels, db_preds)

print(f"\nDistilBERT Test Results:")
print(f"Accuracy:  {db_accuracy:.4f}")
print(f"Precision: {db_precision:.4f}")
print(f"Recall:    {db_recall:.4f}")
print(f"F1 Score:  {db_f1:.4f}")
print(f"Latency:   {db_latency:.4f} ms per email")

# DistilBERT ROC
db_fpr, db_tpr, _ = roc_curve(db_labels, db_proba)
db_auc = auc(db_fpr, db_tpr)
print(f"AUC:       {db_auc:.4f}")

# DistilBERT Confusion Matrix Plot
plt.figure(figsize=(6, 5))
sns.heatmap(db_cm, annot=True, fmt="d", cmap="Oranges",
            xticklabels=["Legitimate", "Phishing"],
            yticklabels=["Legitimate", "Phishing"])
plt.title("DistilBERT - Confusion Matrix (Test Set)")
plt.ylabel("Actual")
plt.xlabel("Predicted")
plt.tight_layout()
plt.savefig("plots/db_confusion_matrix.png", dpi=150)
plt.close()
print("Saved: plots/db_confusion_matrix.png")


# COMBINED COMPARISON PLOTS
print("\nGENERATING COMPARISON PLOTS")

# ROC Curve Comparison
plt.figure(figsize=(8, 6))
plt.plot(rf_fpr, rf_tpr, color="steelblue", lw=2,
         label=f"Random Forest (AUC = {rf_auc:.4f})")
plt.plot(db_fpr, db_tpr, color="darkorange", lw=2,
         label=f"DistilBERT (AUC = {db_auc:.4f})")
plt.plot([0, 1], [0, 1], color="grey", lw=1, linestyle="--", label="Random Chance")
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC Curve Comparison - Random Forest vs DistilBERT")
plt.legend(loc="lower right")
plt.tight_layout()
plt.savefig("plots/roc_curve_comparison.png", dpi=150)
plt.close()
print("Saved: plots/roc_curve_comparison.png")

# Precision-Recall Curve Comparison
rf_pr_precision, rf_pr_recall, _ = precision_recall_curve(test_binary, rf_proba)
db_pr_precision, db_pr_recall, _ = precision_recall_curve(db_labels, db_proba)

plt.figure(figsize=(8, 6))
plt.plot(rf_pr_recall, rf_pr_precision, color="steelblue", lw=2,
         label="Random Forest")
plt.plot(db_pr_recall, db_pr_precision, color="darkorange", lw=2,
         label="DistilBERT")
plt.xlabel("Recall")
plt.ylabel("Precision")
plt.title("Precision-Recall Curve - Random Forest vs DistilBERT")
plt.legend(loc="lower left")
plt.tight_layout()
plt.savefig("plots/precision_recall_comparison.png", dpi=150)
plt.close()
print("Saved: plots/precision_recall_comparison.png")

# Metrics Comparison Bar Chart
metrics = ["Accuracy", "Precision", "Recall", "F1 Score"]
rf_scores = [rf_accuracy, rf_precision, rf_recall, rf_f1]
db_scores = [db_accuracy, db_precision, db_recall, db_f1]

x = np.arange(len(metrics))
width = 0.35

plt.figure(figsize=(10, 6))
bars1 = plt.bar(x - width/2, rf_scores, width, label="Random Forest",
                color="steelblue", alpha=0.85)
bars2 = plt.bar(x + width/2, db_scores, width, label="DistilBERT",
                color="darkorange", alpha=0.85)

for bar in bars1:
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.002,
             f"{bar.get_height():.4f}", ha="center", va="bottom", fontsize=9)
for bar in bars2:
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.002,
             f"{bar.get_height():.4f}", ha="center", va="bottom", fontsize=9)

plt.xticks(x, metrics)
plt.ylim(0.85, 1.02)
plt.ylabel("Score")
plt.title("Model Performance Comparison - Random Forest vs DistilBERT (Test Set)")
plt.legend()
plt.tight_layout()
plt.savefig("plots/metrics_comparison.png", dpi=150)
plt.close()
print("Saved: plots/metrics_comparison.png")

# Latency Comparison
plt.figure(figsize=(6, 5))
model_names = ["Random Forest", "DistilBERT"]
latencies = [rf_latency, db_latency]
colors = ["steelblue", "darkorange"]
bars = plt.bar(model_names, latencies, color=colors, alpha=0.85, width=0.4)
for bar, val in zip(bars, latencies):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
             f"{val:.4f} ms", ha="center", va="bottom", fontsize=10)
plt.ylabel("Average Latency (ms per email)")
plt.title("Inference Latency Comparison (10-run average)")
plt.tight_layout()
plt.savefig("plots/latency_comparison.png", dpi=150)
plt.close()
print("Saved: plots/latency_comparison.png")


# FINAL SUMMARY
print("\nFINAL EVALUATION SUMMARY")
print(f"\n{'Metric':<15} {'Random Forest':>15} {'DistilBERT':>15}")
print(f"{'Accuracy':<15} {rf_accuracy:>15.4f} {db_accuracy:>15.4f}")
print(f"{'Precision':<15} {rf_precision:>15.4f} {db_precision:>15.4f}")
print(f"{'Recall':<15} {rf_recall:>15.4f} {db_recall:>15.4f}")
print(f"{'F1 Score':<15} {rf_f1:>15.4f} {db_f1:>15.4f}")
print(f"{'AUC':<15} {rf_auc:>15.4f} {db_auc:>15.4f}")
print(f"{'Latency (ms)':<15} {rf_latency:>15.4f} {db_latency:>15.4f}")
print("\nPlots saved to: plots/")
print("\nEvaluation complete.")