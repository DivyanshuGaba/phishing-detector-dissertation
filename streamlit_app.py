import streamlit as st

from cli_tool import (
    load_rf,
    build_or_load_directions,
    explain_rf,
    predict_rf,
    load_distilbert,
    predict_and_explain_db,
)

st.set_page_config(page_title="Phishing Detector", page_icon="\U0001F50E", layout="wide")


# MODEL LOADING 
@st.cache_resource(show_spinner="Loading models (first run only)...")
def get_models():
    vectoriser, rf_model = load_rf()
    directions = build_or_load_directions(vectoriser, rf_model)
    tokeniser, db_model, device = load_distilbert()
    return vectoriser, rf_model, directions, tokeniser, db_model, device


# PAGE
st.title("Phishing Detection: Random Forest vs DistilBERT")
st.caption(
    "Local demo. Paste an email below to see both models' prediction, "
    "confidence, latency, and a short explanation of each decision. "
    "Uses the same prediction functions as cli_tool.py."
)

with st.sidebar:
    st.header("About")
    st.markdown(
        "**Random Forest**: TF-IDF + 150-tree classifier. Explanation is "
        "the top Gini-importance features present in the email.\n\n"
        "**DistilBERT**: fine tuned transformer. Explanation is the top "
        "tokens by gradient times input saliency, computed live.\n\n"
        "Both use a 5 run averaged latency measurement with a discarded "
        "warm up call."
    )
    st.divider()
    st.caption("Divyanshu Gaba | 24176025 | Phishing Detection Project")

tab_paste, tab_file = st.tabs(["Paste email", "Upload .txt file"])

with tab_paste:
    subject_input = st.text_input("Subject (optional)", key="subject_paste")
    body_input = st.text_area("Email body", height=220, key="body_paste",
                               placeholder="Paste the email text here...")
    analyse_paste = st.button("Analyse", type="primary", key="btn_paste")
    if analyse_paste:
        st.session_state["run_subject"] = subject_input
        st.session_state["run_body"] = body_input

with tab_file:
    uploaded = st.file_uploader("Choose a .txt file", type=["txt"])
    analyse_file = st.button("Analyse file", type="primary", key="btn_file")
    if analyse_file and uploaded is not None:
        raw = uploaded.read().decode("utf-8", errors="ignore").strip()
        subject = ""
        body = raw
        lines = raw.split("\n", 1)
        if lines[0].lower().startswith("subject:"):
            subject = lines[0][len("subject:"):].strip()
            body = lines[1].strip() if len(lines) > 1 else ""
        st.session_state["run_subject"] = subject
        st.session_state["run_body"] = body


# RUN + DISPLAY
if "run_body" in st.session_state:
    subject = st.session_state["run_subject"]
    body = st.session_state["run_body"]
    text = (subject + " " + body).strip()

    if not text:
        st.error("No email text provided.")
    else:
        st.divider()
        preview = body[:200] + ("..." if len(body) > 200 else "")
        st.markdown(f"**Subject:** {subject if subject else '_(none provided)_'}")
        st.markdown(f"**Body preview:** {preview}")
        st.divider()

        vectoriser, rf_model, directions, tokeniser, db_model, device = get_models()

        with st.spinner("Running both models..."):
            rf_pred, rf_conf, rf_latency = predict_rf(vectoriser, rf_model, text)
            rf_top = explain_rf(vectoriser, rf_model, directions, text)
            db_pred, db_conf, db_latency, db_top = predict_and_explain_db(
                tokeniser, db_model, device, text
            )

        col_rf, col_db = st.columns(2)

        with col_rf:
            st.subheader("Random Forest")
            m1, m2, m3 = st.columns(3)
            m1.metric("Prediction", rf_pred.upper())
            m2.metric("Confidence", f"{rf_conf:.4f}")
            m3.metric("Latency", f"{rf_latency:.2f} ms")
            if rf_top:
                st.markdown("**Top contributing features:**")
                st.table([
                    {"Feature": f, "Importance": f"{imp:.4f}", "Indicates": d}
                    for f, imp, d in rf_top
                ])
            else:
                st.info("No recognised training vocabulary found in this email.")

        with col_db:
            st.subheader("DistilBERT")
            m1, m2, m3 = st.columns(3)
            m1.metric("Prediction", db_pred.upper())
            m2.metric("Confidence", f"{db_conf:.4f}")
            m3.metric("Latency", f"{db_latency:.2f} ms")
            if db_top:
                st.markdown("**Top salient tokens (gradient x input):**")
                st.table([
                    {"Token": t, "Saliency": f"{s:.4f}"} for t, s in db_top
                ])
            else:
                st.info("No salient tokens found.")

        st.divider()
        if rf_pred == db_pred:
            st.success(f"Both models agree: **{rf_pred.upper()}**")
        else:
            st.warning(
                f"Models disagree — Random Forest says **{rf_pred}**, "
                f"DistilBERT says **{db_pred}**"
            )

        speed_ratio = db_latency / rf_latency if rf_latency > 0 else 0
        st.caption(f"Random Forest is {speed_ratio:.1f}x faster than DistilBERT on this email.")
else:
    st.info("Paste an email above, or upload a .txt file, then click Analyse.")