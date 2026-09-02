import pandas as pd
from sklearn.model_selection import train_test_split

# Load the full dataset in the dataframe
df = pd.read_csv("emails_combined.csv")

print(f"Total emails: {len(df)}")
print(f"Label distribution:\n{df['label'].value_counts()}")

# Step 1: Split off 15% as held out test set
train_val, test = train_test_split(
    df,
    test_size=0.15,
    random_state=42,
    stratify=df['label']
)

# Step 2: Split remaining 85% into train (70%) and validation (15%)
train, val = train_test_split(
    train_val,
    test_size=0.176,
    random_state=42,
    stratify=train_val['label']
)

# Save all three splits
train.to_csv("train_combined.csv", index=False)
val.to_csv("val_combined.csv", index=False)
test.to_csv("test_combined.csv", index=False)

print(f"\nSplit complete:")
print(f"Training set:   {len(train)} emails ({len(train)/len(df)*100:.1f}%)")
print(f"Validation set: {len(val)} emails ({len(val)/len(df)*100:.1f}%)")
print(f"Test set:       {len(test)} emails ({len(test)/len(df)*100:.1f}%)")
print(f"\nLabel balance in training set:\n{train['label'].value_counts()}")
print(f"\nLabel balance in validation set:\n{val['label'].value_counts()}")
print(f"\nLabel balance in test set:\n{test['label'].value_counts()}")