import pandas as pd
import pickle
import torch
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification

WIDTH = 66


def section(text):
    print(text.center(WIDTH))


# LOAD TEST SET
test = pd.read_csv("test_combined.csv")
test["text"] = test["subject"].fillna("") + " " + test["body"].fillna("")

# Synthetic categories vs real categories, so FP/FN can be split by source
REAL_CATEGORIES = {"real_enron", "real_historical_phishing"}
test["source"] = test["category"].apply(lambda c: "real" if c in REAL_CATEGORIES else "synthetic")

# RANDOM FOREST PREDICTIONS
with open("rf_pipeline_combined.pkl", "rb") as f:
    rf_pipeline = pickle.load(f)

test["rf_pred"] = rf_pipeline["model"].predict(rf_pipeline["vectoriser"].transform(test["text"]))

# DISTILBERT PREDICTIONS
if torch.backends.mps.is_available():
    device = torch.device("mps")
elif torch.cuda.is_available():
    device = torch.device("cuda")
else:
    device = torch.device("cpu")

tokeniser = DistilBertTokenizer.from_pretrained("distilbert_phishing")
db_model = DistilBertForSequenceClassification.from_pretrained("distilbert_phishing")
db_model.to(device)
db_model.eval()

id2label = {0: "legitimate", 1: "phishing"}
db_preds = []
batch_size = 16
texts = test["text"].tolist()

with torch.no_grad():
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        encodings = tokeniser(batch, truncation=True, padding="max_length", max_length=128, return_tensors="pt")
        encodings = {k: v.to(device) for k, v in encodings.items()}
        outputs = db_model(**encodings)
        batch_preds = torch.argmax(outputs.logits, dim=1).cpu().tolist()
        db_preds.extend([id2label[p] for p in batch_preds])

test["db_pred"] = db_preds


# CORE ANALYSIS FUNCTION - run once per model
def analyse(model_label, pred_col):
    section(f"{model_label} - FAILURE ANALYSIS (TEST SET)")

    df = test.copy()
    df["correct"] = df["label"] == df[pred_col]
    errors = df[~df["correct"]]

    total_errors = len(errors)
    fp = errors[(errors["label"] == "legitimate") & (errors[pred_col] == "phishing")]
    fn = errors[(errors["label"] == "phishing") & (errors[pred_col] == "legitimate")]

    print(f"\nTotal test emails : {len(df)}")
    print(f"Total misclassified: {total_errors}  ({fp.shape[0]} false positives, {fn.shape[0]} false negatives)")

    # FALSE POSITIVE RATE, SPLIT BY SOURCE
    print("\nFALSE POSITIVE RATE BY SOURCE  (legitimate emails wrongly flagged)")
    print(f"  {'Source':<24}{'Legitimate emails':>20}{'False positives':>17}{'FP rate':>9}")
    for source in ["synthetic", "real"]:
        legit_this_source = df[(df["label"] == "legitimate") & (df["source"] == source)]
        fp_this_source = fp[fp["source"] == source]
        n_legit = len(legit_this_source)
        n_fp = len(fp_this_source)
        rate = (n_fp / n_legit * 100) if n_legit else 0.0
        label = "Synthetic (modern)" if source == "synthetic" else "Real (Enron)"
        print(f"  {label:<24}{n_legit:>20}{n_fp:>17}{rate:>8.2f}%")

    # FALSE NEGATIVE RATE, SPLIT BY SOURCE
    print("\nFALSE NEGATIVE RATE BY SOURCE  (phishing emails missed)")
    print(f"  {'Source':<24}{'Phishing emails':>20}{'False negatives':>17}{'FN rate':>9}")
    for source in ["synthetic", "real"]:
        phish_this_source = df[(df["label"] == "phishing") & (df["source"] == source)]
        fn_this_source = fn[fn["source"] == source]
        n_phish = len(phish_this_source)
        n_fn = len(fn_this_source)
        rate = (n_fn / n_phish * 100) if n_phish else 0.0
        label = "Synthetic (modern)" if source == "synthetic" else "Real (historical)"
        print(f"  {label:<24}{n_phish:>20}{n_fn:>17}{rate:>8.2f}%")

    # ERROR BREAKDOWN BY CATEGORY
    print("\nERRORS BY CATEGORY")
    if len(errors):
        counts = errors["category"].value_counts()
        for cat, n in counts.items():
            print(f"  {cat:<30}{n:>10}")
    else:
        print("  No errors.")

    print()
    return {
        "total_errors": total_errors,
        "fp_synthetic_rate": (len(fp[fp["source"] == "synthetic"]) / max(len(df[(df["label"] == "legitimate") & (df["source"] == "synthetic")]), 1)) * 100,
        "fp_real_rate": (len(fp[fp["source"] == "real"]) / max(len(df[(df["label"] == "legitimate") & (df["source"] == "real")]), 1)) * 100,
        "fn_synthetic_rate": (len(fn[fn["source"] == "synthetic"]) / max(len(df[(df["label"] == "phishing") & (df["source"] == "synthetic")]), 1)) * 100,
        "fn_real_rate": (len(fn[fn["source"] == "real"]) / max(len(df[(df["label"] == "phishing") & (df["source"] == "real")]), 1)) * 100,
    }


rf_results = analyse("RANDOM FOREST", "rf_pred")
db_results = analyse("DISTILBERT", "db_pred")


# SIDE BY SIDE COMPARISON (this is the RQ1 evidence)
section("RQ1 EVIDENCE - FALSE POSITIVE RATE ON MODERN EMAIL")
print(f"\n  {'Metric':<32}{'Random Forest':>16}{'DistilBERT':>16}")
print(f"  {'FP rate - synthetic (modern)':<32}{rf_results['fp_synthetic_rate']:>15.2f}%{db_results['fp_synthetic_rate']:>15.2f}%")
print(f"  {'FP rate - real (Enron)':<32}{rf_results['fp_real_rate']:>15.2f}%{db_results['fp_real_rate']:>15.2f}%")
print(f"  {'FN rate - synthetic (modern)':<32}{rf_results['fn_synthetic_rate']:>15.2f}%{db_results['fn_synthetic_rate']:>15.2f}%")
print(f"  {'FN rate - real (historical)':<32}{rf_results['fn_real_rate']:>15.2f}%{db_results['fn_real_rate']:>15.2f}%")
print()