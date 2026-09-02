import pandas as pd
import numpy as np
import pickle
import torch
import matplotlib.pyplot as plt
import seaborn as sns
import os
from collections import defaultdict
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification

os.makedirs("plots", exist_ok=True)

TOP_N = 20
SAMPLE_SIZE = 50
HEATMAP_EXAMPLES = 4

device = torch.device("cpu")

# LOAD DATA AND MODELS
print("Loading test set and models...\n")

test = pd.read_csv("test_combined.csv")
test["text"] = test["subject"].fillna("") + " " + test["body"].fillna("")

with open("rf_pipeline_combined.pkl", "rb") as f:
    rf_pipeline = pickle.load(f)
vectoriser = rf_pipeline["vectoriser"]
rf_model = rf_pipeline["model"]

tokeniser = DistilBertTokenizer.from_pretrained("distilbert_phishing")
db_model = DistilBertForSequenceClassification.from_pretrained("distilbert_phishing")
db_model.to(device)
db_model.eval()

id2label = {0: "legitimate", 1: "phishing"}


# PART 1: RANDOM FOREST - GINI IMPORTANCES
print("PART 1: RANDOM FOREST - GINI FEATURE IMPORTANCES")

feature_names = vectoriser.get_feature_names_out()
importances = rf_model.feature_importances_
top_indices = np.argsort(importances)[::-1][:TOP_N]

all_features = vectoriser.transform(test["text"])
is_phishing = (test["label"] == "phishing").values

rf_rows = []
for idx in top_indices:
    column = all_features[:, idx].toarray().ravel()
    mean_phish = column[is_phishing].mean()
    mean_legit = column[~is_phishing].mean()
    direction = "phishing" if mean_phish > mean_legit else "legitimate"
    rf_rows.append({
        "feature": feature_names[idx],
        "importance": importances[idx],
        "direction": direction,
        "mean_phishing": mean_phish,
        "mean_legitimate": mean_legit
    })

rf_top = pd.DataFrame(rf_rows)

print(f"\n{'Rank':<6}{'Feature':<24}{'Gini':<12}{'Indicates':<12}")
for i, row in rf_top.iterrows():
    print(f"{i+1:<6}{row['feature']:<24}{row['importance']:<12.5f}{row['direction']:<12}")

# Plot with direction encoded by colour
plt.figure(figsize=(10, 7))
colours = ["indianred" if d == "phishing" else "steelblue" for d in rf_top["direction"]]
plt.barh(range(len(rf_top)), rf_top["importance"], color=colours)
plt.yticks(range(len(rf_top)), rf_top["feature"])
plt.gca().invert_yaxis()
plt.xlabel("Gini Importance")
plt.ylabel("Feature")
plt.title(f"Random Forest - Top {TOP_N} Feature Importances by Class Indicated")
handles = [plt.Rectangle((0, 0), 1, 1, color="indianred"),
           plt.Rectangle((0, 0), 1, 1, color="steelblue")]
plt.legend(handles, ["Indicates phishing", "Indicates legitimate"], loc="lower right")
plt.tight_layout()
plt.savefig("plots/rf_gini_directional.png", dpi=150)
plt.close()
print("\nSaved: plots/rf_gini_directional.png")


# PART 2: DISTILBERT - GRADIENT x INPUT ATTRIBUTION
print("\nPART 2: DISTILBERT - GRADIENT x INPUT TOKEN ATTRIBUTION")


def token_saliency(text):
    """Gradient x input attribution for one email.

    Returns the wordpiece tokens, their saliency scores, and the
    predicted label. Special and padding tokens are removed.
    """
    encoding = tokeniser(
        text, truncation=True, padding="max_length",
        max_length=128, return_tensors="pt"
    )
    input_ids = encoding["input_ids"].to(device)
    attention_mask = encoding["attention_mask"].to(device)

    embed_layer = db_model.get_input_embeddings()
    inputs_embeds = embed_layer(input_ids)
    inputs_embeds.retain_grad()

    outputs = db_model(inputs_embeds=inputs_embeds, attention_mask=attention_mask)
    pred_id = torch.argmax(outputs.logits, dim=1).item()

    db_model.zero_grad()
    outputs.logits[0, pred_id].backward()

    # gradient x input, summed over the embedding dimension
    grads = inputs_embeds.grad[0]
    scores = (grads * inputs_embeds[0]).sum(dim=-1).abs().detach().numpy()

    tokens = tokeniser.convert_ids_to_tokens(input_ids[0])
    mask = attention_mask[0].numpy()

    def is_word(token):
        return any(c.isalnum() for c in token)

    keep_tokens = []
    keep_scores = []
    for tok, score, m in zip(tokens, scores, mask):
        if m == 0 or tok in ("[CLS]", "[SEP]", "[PAD]") or not is_word(tok):
            continue
        keep_tokens.append(tok)
        keep_scores.append(float(score))

    return keep_tokens, np.array(keep_scores), id2label[pred_id]


def merge_wordpieces(tokens, scores):
    """Merge ## continuation pieces back into whole words.

    A word takes the maximum saliency of its constituent pieces, so a
    strong signal on any piece is not diluted by averaging.
    """
    words = []
    word_scores = []
    for tok, score in zip(tokens, scores):
        if tok.startswith("##") and words:
            words[-1] += tok[2:]
            word_scores[-1] = max(word_scores[-1], score)
        else:
            words.append(tok)
            word_scores.append(score)
    return words, np.array(word_scores)


# Sample emails for aggregation, balanced across the two classes
sample = pd.concat([
    test[test["label"] == "phishing"].sample(n=SAMPLE_SIZE // 2, random_state=42),
    test[test["label"] == "legitimate"].sample(n=SAMPLE_SIZE // 2, random_state=42)
]).reset_index(drop=True)

print(f"\nComputing attribution for {len(sample)} emails "
      f"({SAMPLE_SIZE // 2} phishing, {SAMPLE_SIZE // 2} legitimate)...")

# Aggregate saliency per word, kept separate by predicted class
agg_phishing = defaultdict(list)
agg_legitimate = defaultdict(list)
per_email = []

for i, row in sample.iterrows():
    tokens, scores, pred = token_saliency(row["text"])
    if len(tokens) == 0:
        continue
    words, word_scores = merge_wordpieces(tokens, scores)

    # normalise within the email so long and short emails contribute equally
    if word_scores.max() > 0:
        word_scores = word_scores / word_scores.max()

    target = agg_phishing if pred == "phishing" else agg_legitimate
    for w, s in zip(words, word_scores):
        target[w].append(s)

    per_email.append({
        "index": i,
        "true_label": row["label"],
        "predicted": pred,
        "category": row["category"],
        "words": words,
        "scores": word_scores
    })

    if (i + 1) % 10 == 0:
        print(f"  processed {i + 1}/{len(sample)}")


def top_words(agg, n=TOP_N, min_count=2):
    """Mean saliency per word, requiring the word to appear more than once
    so that single high-scoring outliers do not dominate the ranking."""
    rows = [(w, float(np.mean(v)), len(v)) for w, v in agg.items() if len(v) >= min_count]
    rows.sort(key=lambda r: r[1], reverse=True)
    return rows[:n]


phish_top = top_words(agg_phishing)
legit_top = top_words(agg_legitimate)

print(f"\nTop {TOP_N} tokens by mean saliency - emails predicted PHISHING")
print(f"{'Rank':<6}{'Token':<24}{'Mean saliency':<16}{'Occurrences':<12}")
for i, (w, s, c) in enumerate(phish_top, start=1):
    print(f"{i:<6}{w:<24}{s:<16.4f}{c:<12}")

print(f"\nTop {TOP_N} tokens by mean saliency - emails predicted LEGITIMATE")
print(f"{'Rank':<6}{'Token':<24}{'Mean saliency':<16}{'Occurrences':<12}")
for i, (w, s, c) in enumerate(legit_top, start=1):
    print(f"{i:<6}{w:<24}{s:<16.4f}{c:<12}")

# Plot aggregated saliency
fig, axes = plt.subplots(1, 2, figsize=(14, 7))
for ax, data, title, colour in [
    (axes[0], phish_top, "Predicted PHISHING", "indianred"),
    (axes[1], legit_top, "Predicted LEGITIMATE", "steelblue")
]:
    words = [r[0] for r in data]
    vals = [r[1] for r in data]
    ax.barh(range(len(words)), vals, color=colour)
    ax.set_yticks(range(len(words)))
    ax.set_yticklabels(words)
    ax.invert_yaxis()
    ax.set_xlabel("Mean saliency (gradient x input)")
    ax.set_title(f"DistilBERT - {title}")
plt.tight_layout()
plt.savefig("plots/distilbert_token_saliency.png", dpi=150)
plt.close()
print("\nSaved: plots/distilbert_token_saliency.png")


# PART 3: PER-EMAIL SALIENCY HEATMAPS
print("\nPART 3: PER-EMAIL SALIENCY HEATMAPS")


def plot_heatmap(entry, filename, per_row=8, max_words=48):
    """Render one email as a grid of tokens shaded by saliency."""
    words = entry["words"][:max_words]
    scores = entry["scores"][:max_words]

    rows = int(np.ceil(len(words) / per_row))
    grid = np.zeros((rows, per_row))
    labels = [["" for _ in range(per_row)] for _ in range(rows)]

    for i, (w, s) in enumerate(zip(words, scores)):
        r, c = divmod(i, per_row)
        grid[r, c] = s
        labels[r][c] = w

    fig, ax = plt.subplots(figsize=(per_row * 1.7, rows * 0.75))
    im = ax.imshow(grid, cmap="Reds", aspect="auto", vmin=0, vmax=1)

    for r in range(rows):
        for c in range(per_row):
            if labels[r][c]:
                shade = "white" if grid[r, c] > 0.6 else "black"
                ax.text(c, r, labels[r][c], ha="center", va="center",
                        fontsize=8, color=shade)

    ax.set_xticks([])
    ax.set_yticks([])
    title = (f"True: {entry['true_label']}  |  Predicted: {entry['predicted']}  "
             f"|  Category: {entry['category']}")
    ax.set_title(title, fontsize=10)
    fig.colorbar(im, ax=ax, label="Normalised saliency", fraction=0.02)
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    plt.close()


# Pick a spread: correct phishing, correct legitimate, and any errors
correct_phish = [e for e in per_email if e["true_label"] == "phishing" and e["predicted"] == "phishing"]
correct_legit = [e for e in per_email if e["true_label"] == "legitimate" and e["predicted"] == "legitimate"]
errors = [e for e in per_email if e["true_label"] != e["predicted"]]

chosen = []
if correct_phish:
    chosen.append(("correct_phishing", correct_phish[0]))
if correct_legit:
    chosen.append(("correct_legitimate", correct_legit[0]))
for j, e in enumerate(errors[:HEATMAP_EXAMPLES - len(chosen)]):
    chosen.append((f"misclassified_{j+1}", e))

for name, entry in chosen:
    fname = f"plots/saliency_heatmap_{name}.png"
    plot_heatmap(entry, fname)
    print(f"Saved: {fname}  ({entry['true_label']} -> {entry['predicted']})")

if not errors:
    print("Note: no misclassified emails in this sample, so only correct "
          "examples are shown.")


# PART 4: RQ2 - SIGNAL OVERLAP BETWEEN THE MODELS
print("\nPART 4: RQ2 - DO THE TWO MODELS RELY ON THE SAME SIGNALS?")

rf_phish_terms = set()
rf_legit_terms = set()
for _, row in rf_top.iterrows():
    terms = row["feature"].split()
    if row["direction"] == "phishing":
        rf_phish_terms.update(terms)
    else:
        rf_legit_terms.update(terms)

db_phish_terms = set(w for w, _, _ in phish_top)
db_legit_terms = set(w for w, _, _ in legit_top)

phish_overlap = rf_phish_terms & db_phish_terms
legit_overlap = rf_legit_terms & db_legit_terms

rf_all = rf_phish_terms | rf_legit_terms
db_all = db_phish_terms | db_legit_terms
overall_overlap = rf_all & db_all
union = rf_all | db_all
jaccard = len(overall_overlap) / len(union) if union else 0.0

print(f"\nRandom Forest  - distinct terms in top {TOP_N}: {len(rf_all)}")
print(f"DistilBERT     - distinct terms in top {TOP_N}: {len(db_all)}")
print(f"\nShared terms overall : {len(overall_overlap)}")
print(f"Jaccard similarity   : {jaccard:.4f}")

print(f"\nShared phishing-indicating terms ({len(phish_overlap)}):")
print(f"  {sorted(phish_overlap) if phish_overlap else 'none'}")
print(f"\nShared legitimate-indicating terms ({len(legit_overlap)}):")
print(f"  {sorted(legit_overlap) if legit_overlap else 'none'}")

print(f"\nTerms unique to Random Forest ({len(rf_all - db_all)}):")
print(f"  {sorted(rf_all - db_all)}")
print(f"\nTerms unique to DistilBERT ({len(db_all - rf_all)}):")
print(f"  {sorted(db_all - rf_all)}")

# Overlap visualisation
plt.figure(figsize=(7, 5))
categories = ["Unique to\nRandom Forest", "Shared", "Unique to\nDistilBERT"]
counts = [len(rf_all - db_all), len(overall_overlap), len(db_all - rf_all)]
bars = plt.bar(categories, counts, color=["steelblue", "mediumpurple", "darkorange"])
for bar, val in zip(bars, counts):
    plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
             str(val), ha="center", va="bottom", fontsize=11)
plt.ylabel("Number of terms")
plt.title(f"Signal Overlap Between Models (top {TOP_N} each)\n"
          f"Jaccard similarity = {jaccard:.3f}")
plt.tight_layout()
plt.savefig("plots/signal_overlap.png", dpi=150)
plt.close()
print("\nSaved: plots/signal_overlap.png")


# SAVE NUMERIC RESULTS FOR THE REPORT
rf_top.to_csv("interpretability_rf_features.csv", index=False)
pd.DataFrame(phish_top, columns=["token", "mean_saliency", "occurrences"]).to_csv(
    "interpretability_db_phishing_tokens.csv", index=False)
pd.DataFrame(legit_top, columns=["token", "mean_saliency", "occurrences"]).to_csv(
    "interpretability_db_legitimate_tokens.csv", index=False)

print("\nSaved numeric results:")
print("  interpretability_rf_features.csv")
print("  interpretability_db_phishing_tokens.csv")
print("  interpretability_db_legitimate_tokens.csv")

print("\nINTERPRETABILITY ANALYSIS COMPLETE")