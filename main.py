import os
import json
import smtplib
from email.mime.text import MIMEText
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import random
import csv
import google.generativeai as genai

# Setup
gemini_key = os.getenv("GEMINI_API_KEY")
if gemini_key:
    genai.configure(api_key=gemini_key)

app = FastAPI()
OTP_STORE = {}
USER_SESSIONS = {} 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class ChatPayload(BaseModel):
    user_message: str
    email: str
    current_step: str

def send_otp_via_email(target_email: str, otp_code: str):
    sender_email = "janarajan04@gmail.com" 
    app_password = os.getenv("GMAIL_APP_PASSWORD")
    if not app_password:
        print("CRITICAL: GMAIL_APP_PASSWORD not set")
        print(f"FALLBACK OTP for {target_email} is: {otp_code}")
        return
    
    msg = MIMEText(f"Welcome to Suyog+!\n\nYour verification code is: {otp_code}")
    msg['Subject'] = "Suyog+ Verification Code"
    msg['From'] = sender_email
    msg['To'] = target_email
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=15)
        server.login(sender_email, app_password)
        server.send_message(msg)
        server.quit()
        print(f"DEBUG: Email successfully sent to {target_email}")
    except Exception as e:
        print(f"Email Error: {e}")
        print("=====================================================")
        print(f"SECURITY BYPASS: The OTP for {target_email} is: {otp_code}")
        print("=====================================================")

def find_top_jobs(user_profile: dict):
    user_dept = user_profile.get("Department", "").lower()
    disability = user_profile.get("Primary Disability", "").lower()
    scored_jobs = []
    
    csv_path = os.path.join(BASE_DIR, 'jobs.csv')
    try:
        with open(csv_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                score = 0
                if user_dept in row.get("Department", "").lower(): score += 5
                disability_text = " ".join([row.get(f"Category of Disabilities - {col}", "") for col in "ABCDE"]).lower()
                if disability in disability_text: score += 10
                scored_jobs.append({"score": score, "title": row.get("Designation", "Job"), "dept": row.get("Department", "")})
    except Exception as e:
        print(f"CSV Read Error: {e}")
        return "### Top Matches\n1. Admin Assistant\n2. Data Entry Clerk"
    
    scored_jobs.sort(key=lambda x: x["score"], reverse=True)
    out = "### Your Top Matches:\n\n"
    for i, job in enumerate(scored_jobs[:3], 1):
        out += f"**{i}. {job['title']}**\n*Dept: {job['dept']}*\n\n"
    return out

@app.post("/api/chat")
def chat_endpoint(payload: ChatPayload):
    msg_orig = payload.user_message.strip()
    email = payload.email.strip().lower()
    step = payload.current_step

    if step == "get_email":
        otp = str(random.randint(1000, 9999))
        OTP_STORE[email] = otp
        send_otp_via_email(email, otp)
        return {"status": "success", "ai_response": "Code sent! Check your email.", "next_step": "verify_code"}

    elif step == "verify_code":
        if OTP_STORE.get(email) == msg_orig.lower():
            del OTP_STORE[email]
            return {"status": "success", "ai_response": "Login success! Introduce yourself (Name & Dept).", "next_step": "get_intro"}
        return {"status": "error", "ai_response": "Wrong code.", "next_step": "verify_code"}

    elif step == "get_intro":
        # ---------------------------------------------------------
        # DUMMY BRAIN TEST: Bypassing Gemini to isolate the error
        # ---------------------------------------------------------
        print(f"DEBUG: Reached get_intro step for {email}")
        
        # Hardcoding the user session data for this test
        USER_SESSIONS[email] = {"Email": email, "Name": "TestUser", "Department": "Administration"}
        
        return {
            "status": "success", 
            "ai_response": "AI Bypass successful! What is your qualification?", 
            "next_step": "get_qualification"
        }

    elif step == "get_qualification":
        if email not in USER_SESSIONS: return {"status": "error", "ai_response": "Session expired.", "next_step": "get_email"}
        USER_SESSIONS[email]["Qualification"] = msg_orig
        return {"status": "success", "ai_response": "Disability type?", "next_step": "get_disability"}

    elif step == "get_disability":
        USER_SESSIONS[email]["Primary Disability"] = msg_orig
        return {"status": "success", "ai_response": "Functional strengths?", "next_step": "get_functional"}

    elif step == "get_functional":
        profile = USER_SESSIONS.get(email, {})
        profile = {k: str(v) for k, v in profile.items()} 
        profile["Functional Strengths"] = msg_orig
        csv_path = os.path.join(BASE_DIR, 'user_database.csv')
        
        file_exists = os.path.isfile(csv_path) and os.stat(csv_path).st_size > 0
        with open(csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["Email", "Name", "Department", "Qualification", "Primary Disability", "Functional Strengths"])
            if not file_exists: 
                writer.writeheader()
            clean_profile = {k: profile.get(k, "N/A") for k in ["Email", "Name", "Department", "Qualification", "Primary Disability", "Functional Strengths"]}
            writer.writerow(clean_profile)
        
        response_text = find_top_jobs(profile)
        USER_SESSIONS.pop(email, None)
        return {"status": "success", "ai_response": response_text, "next_step": "finished"}

    return {"status": "error", "ai_response": "I'm lost.", "next_step": "get_email"}
