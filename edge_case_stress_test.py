import pickle
import torch
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification

WIDTH = 78


# EDGE CASE A: OLD STYLE PHISHING
old_style_phishing = [
    ("Lottery scam", "phishing",
     "CONGRATULATIONS WINNER!!!",
     "Dear Beneficiary, We are pleased to inform you that your email address "
     "has WON the sum of $2,500,000.00 USD in the International Email Lottery "
     "Program. To claim your prize kindly send your full name, address, "
     "telephone number and a copy of your ID to our claims agent immediately. "
     "This offer expires in 48 hours. God bless you."),

    ("Nigerian prince advance-fee", "phishing",
     "URGENT BUSINESS PROPOSAL",
     "Dear Sir/Madam, I am Prince Abassi, son of the late king. I have the sum "
     "of $18,500,000 trapped in a bank and I need a trustworthy foreign partner "
     "to help me transfer these funds. You will receive 30 percent for your "
     "assistance. Please reply urgently with your bank details so we can "
     "proceed with this transaction. This is 100 percent risk free."),

    ("Fake tax threat", "phishing",
     "FINAL NOTICE - IMMEDIATE ACTION REQUIRED",
     "THIS IS YOUR FINAL NOTICE FROM THE TAX DEPARTMENT. Our records indicate "
     "you owe back taxes and a warrant has been issued for your arrest. You "
     "must call our agent within 24 HOURS and pay via gift cards to avoid "
     "legal action. Failure to comply will result in immediate prosecution."),

    ("Romance scam", "phishing",
     "i need your help my love",
     "hello dear how are you today i hope this meet you well. i am writing "
     "to you becouse i need someone i can trust. my late husband left me "
     "alot of money but i cannot access it without help from a foreigner "
     "like you. please contact me back so we can talk more about this "
     "God bless."),

    ("Generic account scare", "phishing",
     "Your Computer Has Been Infected!!",
     "WARNING WARNING WARNING your computer has detected 5 VIRUSES. Click "
     "here now to remove them before your files are deleted forever. Do "
     "not close this window. Call our technical support hotline immediately "
     "for urgent assistance before it is too late."),
]


# EDGE CASE B: MODERN LEGITIMATE EMAIL
novel_legitimate = [
    ("Medical appointment reminder", "legitimate",
     "Appointment reminder: Tuesday 10:30am",
     "Hi Sarah, this is a reminder of your upcoming appointment with Dr. "
     "Chen on Tuesday at 10:30am at the Riverside Health Centre. Please "
     "arrive 10 minutes early to complete registration. If you need to "
     "reschedule, call the clinic on 020 7946 0958. We look forward to "
     "seeing you."),

    ("Calendar meeting invite", "legitimate",
     "Invitation: Weekly Team Sync @ Thu 2pm",
     "You have been invited to the following event. Weekly Team Sync. "
     "Thursday, 2:00pm - 2:30pm. Video call link will be added closer to "
     "the time. Organiser: James Whitfield. Please respond to confirm your "
     "attendance so we can plan the agenda accordingly."),

    ("Flight booking confirmation", "legitimate",
     "Your booking is confirmed - Flight BA1487",
     "Thank you for booking with us. Your flight from London Heathrow to "
     "Edinburgh on 14 August is confirmed. Departure 09:15, arrival 10:35. "
     "Booking reference QX7T2M. Online check-in opens 24 hours before "
     "departure. Baggage allowance and terms are available in your account."),

    ("Streaming service renewal notice", "legitimate",
     "Your subscription renews soon",
     "Hi there, just a heads up that your monthly subscription will renew "
     "on the 3rd of next month at the current rate. No action is needed if "
     "you'd like to continue watching. You can review or manage your plan "
     "any time from your account settings page."),

    ("University enrolment confirmation", "legitimate",
     "Enrolment confirmed for Autumn term",
     "Dear student, this confirms your enrolment onto the MSc Advanced "
     "Computer Science programme for the Autumn term. Your timetable and "
     "reading list are now available on the student portal. If you have "
     "any questions about your modules, please contact your programme tutor."),

    ("Gym membership payment receipt", "legitimate",
     "Payment received - thank you",
     "This confirms we've received your monthly membership payment. Your "
     "membership remains active until the next billing date. You can view "
     "your full payment history and manage your membership from the app "
     "at any time. Thanks for being a member."),
]

CASES = old_style_phishing + novel_legitimate


# LOAD MODELS
print("Loading models...\n")

with open("rf_pipeline_combined.pkl", "rb") as f:
    rf_pipeline = pickle.load(f)
vectoriser = rf_pipeline["vectoriser"]
rf_model = rf_pipeline["model"]

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


def predict_rf(text):
    features = vectoriser.transform([text])
    pred = rf_model.predict(features)[0]
    proba = rf_model.predict_proba(features)[0]
    classes = list(rf_model.classes_)
    conf = proba[classes.index(pred)]
    return pred, conf


def predict_db(text):
    encoding = tokeniser(text, truncation=True, padding="max_length", max_length=128, return_tensors="pt")
    encoding = {k: v.to(device) for k, v in encoding.items()}
    with torch.no_grad():
        outputs = db_model(**encoding)
        probs = torch.softmax(outputs.logits, dim=1)[0]
        pred_id = torch.argmax(probs).item()
        conf = probs[pred_id].item()
    return id2label[pred_id], conf


# RUN AND REPORT
print("EDGE CASE STRESS TEST - OUT OF DISTRIBUTION EMAILS".center(WIDTH))
print(f"\n{len(old_style_phishing)} old-style phishing + {len(novel_legitimate)} novel legitimate "
      f"= {len(CASES)} hand-written cases, none seen during training.\n")

rf_correct = 0
db_correct = 0
rf_errors = []
db_errors = []

header = f"{'#':<3}{'Case':<32}{'Expected':<12}{'RF':<20}{'DistilBERT':<20}"
print(header)

for i, (name, expected, subject, body) in enumerate(CASES, start=1):
    text = subject + " " + body

    rf_pred, rf_conf = predict_rf(text)
    db_pred, db_conf = predict_db(text)

    rf_ok = "OK" if rf_pred == expected else "WRONG"
    db_ok = "OK" if db_pred == expected else "WRONG"

    if rf_pred == expected:
        rf_correct += 1
    else:
        rf_errors.append((name, expected, rf_pred, rf_conf))

    if db_pred == expected:
        db_correct += 1
    else:
        db_errors.append((name, expected, db_pred, db_conf))

    rf_str = f"{rf_pred} ({rf_conf:.2f}) [{rf_ok}]"
    db_str = f"{db_pred} ({db_conf:.2f}) [{db_ok}]"
    print(f"{i:<3}{name:<32}{expected:<12}{rf_str:<20}{db_str:<20}")

print(f"\nRandom Forest : {rf_correct}/{len(CASES)} correct  "
      f"({rf_correct/len(CASES)*100:.1f}%)")
print(f"DistilBERT    : {db_correct}/{len(CASES)} correct  "
      f"({db_correct/len(CASES)*100:.1f}%)\n")

if rf_errors:
    print("Random Forest errors:")
    for name, exp, pred, conf in rf_errors:
        print(f"  - {name}: expected {exp}, predicted {pred} (confidence {conf:.2f})")
    print()

if db_errors:
    print("DistilBERT errors:")
    for name, exp, pred, conf in db_errors:
        print(f"  - {name}: expected {exp}, predicted {pred} (confidence {conf:.2f})")
    print()