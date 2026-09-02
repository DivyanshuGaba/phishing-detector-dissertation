import pandas as pd
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

#  Load splits 
train = pd.read_csv("train_combined.csv")
val = pd.read_csv("val_combined.csv")

print(f"Training on {len(train)} emails...")
print(f"Validating on {len(val)} emails...")

#  Combine subject and body into one text field 
train["text"] = train["subject"].fillna("") + " " + train["body"].fillna("")
val["text"] = val["subject"].fillna("") + " " + val["body"].fillna("")

#  Labels
train_labels = train["label"]
val_labels = val["label"]

# TF-IDF Vectoriser
print("\nBuilding TF-IDF features...")
vectoriser = TfidfVectorizer(
    ngram_range=(1, 2),   # unigrams and bigrams
    max_features=5000,    # top 5000 features
    stop_words="english"
)

train_features = vectoriser.fit_transform(train["text"])
val_features = vectoriser.transform(val["text"])

#  Random Forest 
print("Training Random Forest...")
rf = RandomForestClassifier(
    n_estimators=150,
    max_depth=25,
    random_state=42,
    n_jobs=-1
)

rf.fit(train_features, train_labels)

#  Validation metrics 
val_predictions = rf.predict(val_features)

accuracy  = accuracy_score(val_labels, val_predictions)
precision = precision_score(val_labels, val_predictions, pos_label="phishing")
recall    = recall_score(val_labels, val_predictions, pos_label="phishing")
f1        = f1_score(val_labels, val_predictions, pos_label="phishing")
cm        = confusion_matrix(val_labels, val_predictions, labels=["legitimate", "phishing"])

print(f"\n── Validation Results ")
print(f"Accuracy:  {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall:    {recall:.4f}")
print(f"F1 Score:  {f1:.4f}")
print(f"\nConfusion Matrix:")
print(f"                 Predicted Legitimate  Predicted Phishing")
print(f"Actual Legitimate       {cm[0][0]}                  {cm[0][1]}")
print(f"Actual Phishing         {cm[1][0]}                  {cm[1][1]}")

#  Save the pipeline 
print("\nSaving model...")
with open("rf_pipeline_combined.pkl", "wb") as f:
    pickle.dump({"vectoriser": vectoriser, "model": rf}, f)

print("Saved to rf_pipeline_combined.pkl")
print("\nDone.")