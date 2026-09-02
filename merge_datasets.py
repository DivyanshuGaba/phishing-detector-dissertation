import pandas as pd
from sklearn.model_selection import train_test_split

#  Load your synthetic dataset 
print("Loading synthetic dataset...")
synthetic = pd.read_csv("emails.csv")
print(f"Synthetic emails: {len(synthetic)}")

#  Load the real Kaggle dataset 
print("\nLoading real email dataset...")
real = pd.read_csv("Phishing_Email.csv")
print(f"Real emails before cleaning: {len(real)}")

#  Clean empty and useless rows 
real = real[real['Email Text'].notna()]
real = real[real['Email Text'].str.strip() != '']
real = real[real['Email Text'].str.strip().str.lower() != 'empty']
real = real[real['Email Text'].str.strip().str.lower() != 'nan']
real = real[real['Email Text'].str.len() > 50]
print(f"Real emails after cleaning: {len(real)}")

#  Sample 2500 legitimate and 2500 phishing from real data 
real_legit = real[real['Email Type'] == 'Safe Email'].sample(
    n=2500, random_state=42
)
real_phish = real[real['Email Type'] == 'Phishing Email'].sample(
    n=2500, random_state=42
)

#  Standardise real data columns to match your synthetic format 
real_legit_clean = pd.DataFrame({
    'id': range(len(real_legit)),
    'label': 'legitimate',
    'category': 'real_enron',
    'subject': '',
    'body': real_legit['Email Text'].values
})

real_phish_clean = pd.DataFrame({
    'id': range(len(real_phish)),
    'label': 'phishing',
    'category': 'real_historical_phishing',
    'subject': '',
    'body': real_phish['Email Text'].values
})

#  Combine everything
combined = pd.concat([
    synthetic,
    real_legit_clean,
    real_phish_clean
], ignore_index=True)

# Reset IDs 
combined['id'] = range(len(combined))

#  Check balance 
print(f"\nCombined dataset: {len(combined)} emails")
print(f"Label distribution:\n{combined['label'].value_counts()}")

#  Save combined dataset 
combined.to_csv("emails_combined.csv", index=False)
print("\nSaved to emails_combined.csv")