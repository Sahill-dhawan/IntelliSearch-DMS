import streamlit as st
import re
import pandas as pd
import hashlib
import plotly.express as px
from PyPDF2 import PdfReader
from docx import Document

# ================= LOGIN =================
USERS = {"admin": "admin123"}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("🔐 HireScan Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in USERS and USERS[u] == p:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Wrong credentials")

if not st.session_state.logged_in:
    login()
    st.stop()

# ================= UI =================
st.title("📊 HireScan ATS ")

# ================= FILE READER =================
def read_file(file):
    text = ""

    if file.name.endswith(".pdf"):
        reader = PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ""

    elif file.name.endswith(".docx"):
        doc = Document(file)
        text = "\n".join([p.text for p in doc.paragraphs])

    else:
        text = file.read().decode("utf-8")

    return text.lower()

# ================= KEYWORDS =================
def extract_keywords(text):
    words = re.findall(r"\b[a-zA-Z]{3,}\b", text)
    stop = {"the","and","for","with","this","that","you","are","will","our","from","into","have","job","role"}
    return list(set([w for w in words if w not in stop]))

def score(text, keywords):
    score = 0
    matched = []

    for k in keywords:
        if k in text:
            score += 1
            matched.append(k)

    return score, matched

def experience(text):
    m = re.findall(r"(\d+)\s*(year|years)", text)
    return int(m[0][0]) if m else 0

def hash_file(text):
    return hashlib.md5(text.encode()).hexdigest()

# ================= SIDEBAR =================
st.sidebar.header("Recruiter Panel")

files = st.sidebar.file_uploader("Upload Resumes", type=["pdf","docx","txt"], accept_multiple_files=True)
jd_file = st.sidebar.file_uploader("Upload JD", type=["pdf","docx","txt"])

manual_keywords = st.sidebar.text_input("Manual Keywords (optional)", placeholder="python, sql, excel")

min_exp = st.sidebar.slider("Min Experience", 0, 10, 0)
top_percent = st.sidebar.slider("Top % Cutoff", 10, 100, 30)

run = st.sidebar.button("Run ATS")

# ================= KEYWORDS BUILD =================
jd_keywords = []

if jd_file:
    jd_text = read_file(jd_file)
    jd_keywords = extract_keywords(jd_text)

manual_list = [k.strip().lower() for k in manual_keywords.split(",") if k.strip()]

keywords = list(set(jd_keywords + manual_list))

# ================= MAIN =================
if run:

    if not files:
        st.warning("Upload resumes")
        st.stop()

    if not keywords:
        st.warning("Add JD or manual keywords")
        st.stop()

    results = []
    seen = set()

    progress = st.progress(0, text="Analyzing resumes...")

    for i, f in enumerate(files):

        text = read_file(f)
        h = hash_file(text)

        if h in seen:
            continue
        seen.add(h)

        sc, matched = score(text, keywords)
        exp = experience(text)

        match_pct = round((sc / len(keywords)) * 100, 2)

        status = "❌ Rejected"
        if exp >= min_exp and match_pct >= top_percent:
            status = "✅ Shortlisted"

        results.append({
            "Resume": f.name,
            "Score": sc,
            "Match %": match_pct,
            "Experience": exp,
            "Status": status,
            "Matched Keywords": ", ".join(matched)
        })

        progress.progress((i+1)/len(files), text=f"Processing {f.name}")

    df = pd.DataFrame(results)
    df = df.sort_values("Score", ascending=False)

    shortlisted = df[df["Status"] == "✅ Shortlisted"]

    # ================= METRICS =================
    c1, c2, c3 = st.columns(3)
    c1.metric("Total", len(df))
    c2.metric("Shortlisted", len(shortlisted))
    c3.metric("Rejection %", f"{round(100 - len(shortlisted)/len(df)*100, 2)}%")

    st.divider()

    # ================= TABLE =================
    st.dataframe(df, use_container_width=True)

    # ================= CHART =================
    fig = px.bar(df, x="Resume", y="Match %", color="Status")
    st.plotly_chart(fig, use_container_width=True)

    # ================= DOWNLOAD =================
    st.download_button(
        "Download Report",
        df.to_csv(index=False),
        "ats_report.csv",
        "text/csv"
    )