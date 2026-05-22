HireScan ATS is a Streamlit-based Resume Screening System that automates the process of analyzing and ranking resumes based on a Job Description (JD).
It acts as a mini Applicant Tracking System (ATS) that evaluates resumes using keyword matching, experience detection, and scoring logic to help recruiters shortlist candidates efficiently.

💡 Features
📂 Upload multiple resumes (PDF, DOCX, TXT)
📄 Upload Job Description (JD) for smart keyword extraction
🧠 Automatic keyword extraction & matching
📊 Resume scoring based on match percentage
📅 Experience detection from resume text
✅ Auto Shortlisting / Rejection system
🔁 Duplicate resume detection using hashing
📈 Interactive charts using Plotly
📥 Download final ATS report as CSV
🔐 Simple login authentication system (demo)

🛠 Tech Stack
Python 🐍
Streamlit 🎈
Pandas 📊
Plotly 📈
PyPDF2 📄
python-docx 📑
Regex (Text Processing)
Hashlib (Duplicate detection)

⚙️ How It Works

📄 Upload Job Description (JD)
🔑 System extracts important keywords
📂 Upload multiple resumes
🧠 Each resume is processed and scored based on:

Keyword matches
Experience years
Relevance %

📊 Final Output:

Resume score
Match percentage
Shortlisted / Rejected status
Matched keywords
Graph visualization

📥 Download full ATS report as CSV
