# Detecting Modern, LLM-Style Phishing

**A Synthetic and Real-Data Comparison of Random Forest and DistilBERT**

MSc Advanced Computer Science dissertation
Author: Divyanshu Gaba

## Overview

Commercial email filters still miss a meaningful share of modern, LLM-generated phishing — polished, grammatically clean messages that no longer carry the typos and awkward phrasing older spam filters were trained to catch. This project builds an end-to-end pipeline to study that gap: a classical machine learning baseline (TF-IDF + Random Forest) is benchmarked against a fine-tuned transformer (DistilBERT) on a shared dataset of synthetic and real phishing/legitimate emails, then both models are compared not just on accuracy but on *what they actually learned* — using feature-importance and saliency analysis to see whether the two approaches catch phishing for the same reasons or different ones.

A critical data leakage bug was diagnosed and fixed during the project (an initial F1 score of 1.0000 turned out to be a red flag, not a result), which became a core part of the dissertation's methodology discussion around benchmark validity.

## Key Findings

| | TF-IDF + Random Forest | Fine-tuned DistilBERT |
|---|---|---|
| F1 score | 0.9530 | 0.9907 |
| Inference latency | baseline | ~5.9x slower |
| Interpretability method | Gini feature importance | Gradient-based saliency |

- **Feature overlap between the two models: just 5.4%** (Jaccard similarity) — despite both achieving high, comparable accuracy, they rely on almost entirely different signals in the text to make their decisions.
- The final dataset combines **10,002 emails**: synthetic phishing/legitimate pairs generated for this project, plus real Enron legitimate emails and real historical phishing emails, specifically to close the data leakage gap found in the synthetic-only version and give both models a genuine generalisation test.

## Pipeline

Scripts are designed to run in this order:

| # | Script | Purpose |
|---|---|---|
| 1 | `generate_emails.py` | Generates the synthetic legitimate/phishing email dataset (`emails.csv`) |
| 2 | `merge_datasets.py` | Merges the synthetic set with real Enron and historical phishing emails (Kaggle `Phishing_Email.csv`) into `emails_combined.csv`, fixing the data leakage issue found in the synthetic-only version |
| 3 | `split_dataset.py` | Splits the combined dataset into train/validation/test sets |
| 4 | `train_random_forest.py` | Trains the TF-IDF + Random Forest pipeline, saves `rf_pipeline_combined.pkl` |
| 5 | `train_distilbert.py` | Fine-tunes DistilBERT for binary classification, saves the model to `distilbert_phishing/` |
| 6 | `evaluate_and_plot.py` | Evaluates both models on the test set and generates comparison plots |
| 7 | `analyse_errors.py` | Breaks down misclassifications for both models |
| 8 | `print_evaluation_summary.py` | Prints a consolidated results summary (accuracy, precision, recall, F1, latency) |
| — | `streamlit_app.py` | Interactive demo: classify an email live and compare both models side by side, including interpretability output |

## Methodology Summary

1. **Dataset generation** — synthetic phishing and legitimate emails built from templated subjects/bodies across multiple categories (banking, delivery, IT support, etc.)
2. **Leakage fix** — an early version leaked the label through URL patterns injected into phishing emails, producing a suspicious F1 of 1.0000. Fixed by removing the leaking URL-generation logic and merging in real-world email data so both classes draw from genuinely independent sources.
3. **Baseline model** — TF-IDF vectorisation (unigrams + bigrams, 5,000 features) feeding a Random Forest classifier (150 trees, max depth 25).
4. **Transformer model** — `distilbert-base-uncased` fine-tuned for 3 epochs with AdamW.
5. **Evaluation** — accuracy, precision, recall, F1, and inference latency (5-run averaged, discarding a warm-up call) on a held-out test set.
6. **Interpretability** — Gini feature importance for the Random Forest vs. gradient-based saliency for DistilBERT, compared via Jaccard similarity over each model's top features.

## Running it locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install pandas scikit-learn torch transformers streamlit matplotlib seaborn

python3 generate_emails.py
python3 merge_datasets.py        # requires Phishing_Email.csv (Kaggle) in the project root
python3 split_dataset.py
python3 train_random_forest.py
python3 train_distilbert.py      # ~15 minutes on Apple Silicon (MPS)
python3 evaluate_and_plot.py
python3 analyse_errors.py
python3 print_evaluation_summary.py
```

**Live demo:**
```bash
streamlit run streamlit_app.py
```

## Data & models

Raw datasets, trained model weights, and generated plots are not committed to this repository (see `.gitignore`) — they're reproducible by running the pipeline above in order. The real-email component requires the [Phishing Email Dataset](https://www.kaggle.com/datasets/subhajournal/phishingemails) from Kaggle, placed as `Phishing_Email.csv` in the project root before running `merge_datasets.py`.

## Author

**Divyanshu Gaba** — MSc Advanced Computer Science dissertation
