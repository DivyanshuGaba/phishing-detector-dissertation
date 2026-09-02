import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
from torch.optim import AdamW
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import time

#  Device setup 
if torch.backends.mps.is_available():
    device = torch.device("mps")
    print("Using Apple Silicon MPS")
elif torch.cuda.is_available():
    device = torch.device("cuda")
    print("Using NVIDIA CUDA")
else:
    device = torch.device("cpu")
    print("Using CPU")

#  Load data 
print("\nLoading data...")
train = pd.read_csv("train_combined.csv")
val = pd.read_csv("val_combined.csv")

train["text"] = train["subject"].fillna("") + " " + train["body"].fillna("")
val["text"] = val["subject"].fillna("") + " " + val["body"].fillna("")

#  Label encoding 
label2id = {"legitimate": 0, "phishing": 1}
train["label_id"] = train["label"].map(label2id)
val["label_id"] = val["label"].map(label2id)

print(f"Training samples: {len(train)}")
print(f"Validation samples: {len(val)}")

#  Tokeniser 
print("\nLoading DistilBERT tokeniser...")
tokeniser = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")

#  Dataset class 
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

#  Create datasets 
train_dataset = EmailDataset(
    train["text"].tolist(),
    train["label_id"].tolist(),
    tokeniser
)
val_dataset = EmailDataset(
    val["text"].tolist(),
    val["label_id"].tolist(),
    tokeniser
)

#  Data loaders 
train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=8, shuffle=False)

#  Load model 
print("\nLoading DistilBERT model...")
model = DistilBertForSequenceClassification.from_pretrained(
    "distilbert-base-uncased",
    num_labels=2
)
model = model.to(device)

#  Optimiser 
optimiser = AdamW(model.parameters(), lr=2e-5, weight_decay=0.01)

#  Training loop 
print("\nStarting training...")
EPOCHS = 3

for epoch in range(EPOCHS):
    model.train()
    total_loss = 0
    start_time = time.time()

    for batch_idx, batch in enumerate(train_loader):
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["label"].to(device)

        optimiser.zero_grad()
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels
        )
        loss = outputs.loss
        loss.backward()
        optimiser.step()
        total_loss += loss.item()

        if (batch_idx + 1) % 100 == 0:
            print(f"  Epoch {epoch+1} | Batch {batch_idx+1}/{len(train_loader)} | Loss: {loss.item():.4f}")

    avg_loss = total_loss / len(train_loader)
    elapsed = time.time() - start_time
    print(f"\nEpoch {epoch+1} complete | Avg Loss: {avg_loss:.4f} | Time: {elapsed:.1f}s")

    #  Validation 
    model.eval()
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for batch in val_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["label"].to(device)

            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask
            )
            preds = torch.argmax(outputs.logits, dim=1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    accuracy  = accuracy_score(all_labels, all_preds)
    precision = precision_score(all_labels, all_preds)
    recall    = recall_score(all_labels, all_preds)
    f1        = f1_score(all_labels, all_preds)

    print(f"Validation | Accuracy: {accuracy:.4f} | Precision: {precision:.4f} | Recall: {recall:.4f} | F1: {f1:.4f}")

#  Save model 
print("\nSaving model...")
model.save_pretrained("distilbert_phishing")
tokeniser.save_pretrained("distilbert_phishing")
print("Model saved to distilbert_phishing/")
print("\nDone.")