import streamlit as st
import PyPDF2
import io
import os
from openai import OpenAI, RateLimitError
from dotenv import load_dotenv

load_dotenv()
st.set_page_config(page_title="AI Resume Critique", page_icon="🤖",layout = "centered")


st.title("HireLens - AI Resume Critique")
 
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "openai/gpt-oss-20b")

upload_file = st.file_uploader("Upload your resume (PDF or TXT)", type = ["pdf","txt"])
job_role = st.text_input("Enter the job role your are applying (Optional) ")

analyse = st.button("Analyse Resume")

def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text =""
    for page in pdf_reader.pages:
        text += (page.extract_text() or "") + '\n'
    return text

def extract_text_from_file(upload_file):
    file_bytes = upload_file.getvalue()
    is_pdf = upload_file.type == "application/pdf" or upload_file.name.lower().endswith(".pdf")
    if is_pdf:
        return extract_text_from_pdf(io.BytesIO(file_bytes))

    try:
        return file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        return file_bytes.decode("cp1252")

if analyse and upload_file:
    try:
        file_cont = extract_text_from_file(upload_file)

        if not file_cont.strip():
            st.error("File does not have any content")
            st.stop()

        
        prompt = f"""You are an expert Resume Critic and ATS-focused Career Advisor. Analyze the user's resume objectively and provide clear, practical, and actionable feedback.

Your goals are to:
- Identify weaknesses, errors, and missing information.
- Check ATS compatibility and keyword usage.
- Evaluate clarity, structure, readability, and professionalism.
- Assess skills, projects, education, and work experience.
- Check whether achievements demonstrate measurable impact.
- If a job description is provided, compare the resume against it and identify matches, missing skills, and relevant keywords.
- Never invent skills, experience, achievements, metrics, or qualifications.

ANALYSIS RULES:

1. Prioritize important issues over minor formatting or grammar problems.
2. Be honest and constructive. Do not give unnecessarily high scores.
3. Give specific recommendations instead of generic advice.
4. Preserve the candidate's actual experience and never encourage false claims.
5. For weak bullet points, explain the problem and provide an improved version when possible.
6. If a metric or detail is missing, suggest adding it rather than creating one.
7. Do not recommend keyword stuffing.
8. Specific improvements for {job_role if job_role else 'general job applications'}

OUTPUT FORMAT:

1. OVERALL SCORE
Give a score out of 100 and briefly explain the main strengths and weaknesses.

2. SCORE BREAKDOWN
- Content & Relevance: /25
- Experience & Achievements: /20
- ATS Compatibility: /20
- Skills & Technical Strength: /15
- Structure & Readability: /10
- Grammar & Writing: /10

3. TOP IMPROVEMENTS
List the 5 most important improvements. Classify each as:
- High Priority
- Medium Priority
- Low Priority

For each improvement, provide:
- Problem
- Why it matters
- Recommended fix

4. SECTION REVIEW
Review the relevant sections:
- Summary/Objective
- Experience
- Projects
- Skills
- Education
- Certifications/Achievements

Mention strengths and specific improvements.

5. BULLET IMPROVEMENTS
For weak bullet points, show:
Current: [original bullet]
Improved: [better version]

Never fabricate information.

6. ATS ANALYSIS
Give an ATS Readiness score out of 100.

Mention:
- ATS-friendly elements
- ATS problems
- Important keywords
- Missing or weak keywords

If a job description is provided, classify keywords as:
- Present
- Weak/Indirect
- Missing

7. RECRUITER PERSPECTIVE
Briefly explain what would make a recruiter continue reading and what could cause rejection.

8. FINAL ACTION PLAN
Provide a short prioritized checklist of the most important changes to make.

Keep the response concise, professional, structured, and easy to scan. Focus on actionable improvements rather than lengthy explanations.
Resume content:
{file_cont}""" 

        if not NVIDIA_API_KEY:
            st.error("NVIDIA_API_KEY is not configured. Add it to your .env file.")
            st.stop()

        client = OpenAI(api_key=NVIDIA_API_KEY, base_url=NVIDIA_BASE_URL)
        response = client.chat.completions.create(
            model=NVIDIA_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert resume reviewer with years of experience in HR and recruitment."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens = 1000
        )
        st.markdown("### Analysis Results ")
        st.markdown(response.choices[0].message.content)

    except RateLimitError as e:
        if getattr(e, "code", None) == "insufficient_quota":
            st.error(
                "Your NVIDIA API account has no credits remaining. "
                "Check your NVIDIA API plan or use a model with available quota."
            )
        else:
            st.error(f"NVIDIA API rate limit reached: {e}")
    except Exception as e:
        st.error(f"An error occurred: {e}")
           

