import pandas as pd
import pickle
import numpy as np

#  Load validation set 
val = pd.read_csv("val_combined.csv")
val["text"] = val["subject"].fillna("") + " " + val["body"].fillna("")

#  Load trained model 
with open("rf_pipeline_combined.pkl", "rb") as f:
    pipeline = pickle.load(f)

vectoriser = pipeline["vectoriser"]
model = pipeline["model"]

#  Make predictions 
val_features = vectoriser.transform(val["text"])
val["predicted"] = model.predict(val_features)
val["correct"] = val["label"] == val["predicted"]

#  Pull out misclassified emails 
errors = val[val["correct"] == False].copy()

print(f"Total misclassified: {len(errors)}")
print(f"\nBreakdown:")
print(errors.groupby(["label", "predicted"]).size())

#  False Positives: legitimate flagged as phishing 
fp = errors[(errors["label"] == "legitimate") & (errors["predicted"] == "phishing")]
print(f"\nFALSE POSITIVES ({len(fp)})")
print("Legitimate emails wrongly flagged as phishing:\n")
for i, row in fp.iterrows():
    print(f"Category: {row['category']}")
    print(f"Subject:  {row['subject']}")
    print(f"Body:     {str(row['body'])[:200]}")

#  False Negatives: phishing missed as legitimate 
fn = errors[(errors["label"] == "phishing") & (errors["predicted"] == "legitimate")]
print(f"\nFALSE NEGATIVES ({len(fn)})")
print("Phishing emails that slipped through as legitimate:\n")
for i, row in fn.iterrows():
    print(f"Category: {row['category']}")
    print(f"Subject:  {row['subject']}")
    print(f"Body:     {str(row['body'])[:200]}")

#  Category breakdown of errors 
print(f"\nERROR BREAKDOWN BY CATEGORY")
print(errors["category"].value_counts())