import argparse
import os
import sys
import time
import pickle
import numpy as np
import pandas as pd
import torch
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification

DIRECTIONS_CACHE = "rf_feature_directions.csv"
WIDTH = 64


def section(text):
    print(text.center(WIDTH))


# INPUT HANDLING
def get_input_text(args):
    if args.file:
        with open(args.file, "r", encoding="utf-8", errors="ignore") as f:
            raw = f.read()
    elif args.text:
        raw = args.text
    else:
        print("Paste the email text below, then press Ctrl-D (Mac/Linux) "
              "or Ctrl-Z then Enter (Windows) to finish:\n")
        raw = sys.stdin.read()

    raw = raw.strip()
    subject = args.subject or ""
    body = raw

    # allow "Subject: " as the first line if no subject was given
    lines = raw.split("\n", 1)
    if not subject and lines[0].lower().startswith("subject:"):
        subject = lines[0][len("subject:"):].strip()
        body = lines[1].strip() if len(lines) > 1 else ""

    if not raw:
        print("No email text provided.")
        sys.exit(1)

    return subject, body


# RANDOM FOREST - LOAD + EXPLAIN
def load_rf():
    with open("rf_pipeline_combined.pkl", "rb") as f:
        pipeline = pickle.load(f)
    return pipeline["vectoriser"], pipeline["model"]


def build_or_load_directions(vectoriser, rf_model):
    """Direction (which class each feature points toward) isn't part of
    Gini importance itself, so it's derived once from the test set and
    cached to disk. Degrades gracefully if the cache and the test set
    are both unavailable - importance is still shown, just not direction.
    """
    if os.path.exists(DIRECTIONS_CACHE):
        return pd.read_csv(DIRECTIONS_CACHE).set_index("feature")

    if not os.path.exists("test_combined.csv"):
        return None

    print("Building feature-direction reference (first run only)...")
    test = pd.read_csv("test_combined.csv")
    test["text"] = test["subject"].fillna("") + " " + test["body"].fillna("")

    dense = vectoriser.transform(test["text"]).toarray()
    is_phishing = (test["label"] == "phishing").values
    names = vectoriser.get_feature_names_out()
    importances = rf_model.feature_importances_

    mean_phish = dense[is_phishing].mean(axis=0)
    mean_legit = dense[~is_phishing].mean(axis=0)
    direction = np.where(mean_phish > mean_legit, "phishing", "legitimate")

    df = pd.DataFrame({
        "feature": names,
        "importance": importances,
        "direction": direction
    }).set_index("feature")
    df.to_csv(DIRECTIONS_CACHE)
    print(f"Saved: {DIRECTIONS_CACHE}\n")
    return df


def explain_rf(vectoriser, rf_model, directions, text, top_n=5):
    """Of the features that actually appear in this email, return the
    top N by global Gini importance - a per-email explanation grounded
    in the model's overall learned importances."""
    vec = vectoriser.transform([text])
    present_idx = vec.nonzero()[1]
    if len(present_idx) == 0:
        return []

    names = vectoriser.get_feature_names_out()
    importances = rf_model.feature_importances_

    rows = []
    for idx in present_idx:
        name = names[idx]
        imp = importances[idx]
        if directions is not None and name in directions.index:
            direction = directions.loc[name, "direction"]
        else:
            direction = "unknown"
        rows.append((name, imp, direction))

    rows.sort(key=lambda r: r[1], reverse=True)
    return rows[:top_n]


def predict_rf(vectoriser, rf_model, text, n_runs=5):
    features = vectoriser.transform([text])

    rf_model.predict(features)
    timings = []
    for _ in range(n_runs):
        start = time.perf_counter()
        pred = rf_model.predict(features)[0]
        end = time.perf_counter()
        timings.append((end - start) * 1000)
    proba = rf_model.predict_proba(features)[0]
    classes = list(rf_model.classes_)
    conf = proba[classes.index(pred)]
    return pred, conf, np.mean(timings)


# DISTILBERT - LOAD + EXPLAIN
def load_distilbert():
    device = torch.device("cpu")  # single-email latency, consistent across machines
    tokeniser = DistilBertTokenizer.from_pretrained("distilbert_phishing")
    model = DistilBertForSequenceClassification.from_pretrained("distilbert_phishing")
    model.to(device)
    model.eval()
    return tokeniser, model, device


def predict_and_explain_db(tokeniser, model, device, text, top_n=5, n_runs=5):
    encoding = tokeniser(text, truncation=True, padding="max_length",
                          max_length=128, return_tensors="pt")
    input_ids = encoding["input_ids"].to(device)
    attention_mask = encoding["attention_mask"].to(device)

    # warm-up + averaged latency, same fix as the RF side
    with torch.no_grad():
        model(input_ids=input_ids, attention_mask=attention_mask)
    timings = []
    with torch.no_grad():
        for _ in range(n_runs):
            start = time.perf_counter()
            model(input_ids=input_ids, attention_mask=attention_mask)
            end = time.perf_counter()
            timings.append((end - start) * 1000)

    # separate pass with grad enabled for attribution
    embed_layer = model.get_input_embeddings()
    inputs_embeds = embed_layer(input_ids)
    inputs_embeds.retain_grad()

    outputs = model(inputs_embeds=inputs_embeds, attention_mask=attention_mask)
    probs = torch.softmax(outputs.logits, dim=1)[0]
    pred_id = torch.argmax(probs).item()
    conf = probs[pred_id].item()

    model.zero_grad()
    outputs.logits[0, pred_id].backward()
    grads = inputs_embeds.grad[0]
    scores = (grads * inputs_embeds[0]).sum(dim=-1).abs().detach().numpy()

    tokens = tokeniser.convert_ids_to_tokens(input_ids[0])
    mask = attention_mask[0].numpy()

    words, word_scores = [], []
    for tok, score, m in zip(tokens, scores, mask):
        if m == 0 or tok in ("[CLS]", "[SEP]", "[PAD]"):
            continue
        if tok.startswith("##") and words:
            words[-1] += tok[2:]
            word_scores[-1] = max(word_scores[-1], float(score))
        else:
            words.append(tok)
            word_scores.append(float(score))

    def is_word(token):
        return any(c.isalnum() for c in token)

    ranked = sorted(
        [(w, s) for w, s in zip(words, word_scores) if is_word(w)],
        key=lambda r: r[1], reverse=True
    )
    id2label = {0: "legitimate", 1: "phishing"}
    return id2label[pred_id], conf, np.mean(timings), ranked[:top_n]


# MAIN
def main():
    parser = argparse.ArgumentParser(
        description="Compare Random Forest and DistilBERT on a single email, "
                     "with a short explanation of each prediction."
    )
    parser.add_argument("--file", type=str, help="Path to a .txt file containing the email")
    parser.add_argument("--text", type=str, help="Raw email text")
    parser.add_argument("--subject", type=str, default="", help="Optional subject line")
    args = parser.parse_args()

    subject, body = get_input_text(args)
    text = (subject + " " + body).strip()

    section("PHISHING DETECTION - EMAIL ANALYSIS")
    print(f"\n  Subject : {subject if subject else '(none provided)'}")
    preview = body[:100] + ("..." if len(body) > 100 else "")
    print(f"  Body    : {preview}\n")

    print("\nLoading models...")
    vectoriser, rf_model = load_rf()
    directions = build_or_load_directions(vectoriser, rf_model)
    tokeniser, db_model, device = load_distilbert()

    # RANDOM FOREST
    rf_pred, rf_conf, rf_latency = predict_rf(vectoriser, rf_model, text)
    rf_top = explain_rf(vectoriser, rf_model, directions, text)

    print("\nRANDOM FOREST")
    print(f"  Prediction  : {rf_pred}")
    print(f"  Confidence  : {rf_conf:.4f}")
    print(f"  Latency     : {rf_latency:.3f} ms  (5 run average, warmup excluded)")
    if rf_top:
        print("\n  Top contributing features (present in this email):")
        for i, (feat, imp, direction) in enumerate(rf_top, start=1):
            print(f"    {i}. {feat:<20} importance {imp:.4f}  -> {direction}")
    else:
        print("\n  No recognised vocabulary from training found in this email.")

    # DISTILBERT
    db_pred, db_conf, db_latency, db_top = predict_and_explain_db(
        tokeniser, db_model, device, text
    )

    print("\nDISTILBERT")
    print(f"  Prediction  : {db_pred}")
    print(f"  Confidence  : {db_conf:.4f}")
    print(f"  Latency     : {db_latency:.3f} ms  (5 run average, warmup excluded)")
    if db_top:
        print("\n  Top salient tokens (gradient x input):")
        for i, (tok, score) in enumerate(db_top, start=1):
            print(f"    {i}. {tok:<20} saliency {score:.4f}")

    # SUMMARY
    print()
    section("SUMMARY")
    if rf_pred == db_pred:
        print(f"\n  Both models agree: {rf_pred.upper()}")
    else:
        print(f"\n  Models disagree:")
        print(f"    Random Forest -> {rf_pred}")
        print(f"    DistilBERT    -> {db_pred}")
    print(f"\n  Speed: Random Forest is {db_latency / rf_latency:.1f}x faster "
          f"than DistilBERT on this email")
    print()


if __name__ == "__main__":
    main()