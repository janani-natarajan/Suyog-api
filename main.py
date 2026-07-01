import os
import json
import smtplib
from email.mime.text import MIMEText
from fastapi import FastAPI
from pydantic import BaseModel
import random
import csv
import google.generativeai as genai

# Setup Gemini
gemini_key = os.getenv("GEMINI_API_KEY")
if gemini_key:
    genai.configure(api_key=gemini_key)

app = FastAPI()

OTP_STORE = {}
USER_SESSIONS = {} 

class ChatPayload(BaseModel):
    user_message: str
    email: str
    current_step: str

def send_otp_via_email(target_email: str, otp_code: str):
    sender_email = "janarajan04@gmail.com" 
    app_password = os.getenv("GMAIL_APP_PASSWORD")
    msg = MIMEText(f"Welcome to Suyog+!\n\nYour verification code is: {otp_code}")
    msg['Subject'] = "Suyog+ Verification Code"
    msg['From'] = sender_email
    msg['To'] = target_email
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls() 
        server.login(sender_email, app_password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Email Error: {e}")

def extract_info_with_gemini(text: str):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Extract the user's name and department from: "{text}"
        Departments: Administration, IT, HR, Finance, Accounts, Postal.
        Return ONLY JSON: {{"name": "...", "department": "..."}}
        """
        response = model.generate_content(prompt)
        return json.loads(response.text.replace('```json', '').replace('```', '').strip())
    except:
        return {"name": "User", "department": "Unknown"}

def find_top_jobs(user_profile: dict):
    user_dept = user_profile.get("Department", "").lower()
    disability = user_profile.get("Primary Disability", "").lower()
    
    scored_jobs = []
    try:
        with open('jobs.csv', mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                score = 0
                if user_dept in row.get("Department", "").lower(): score += 5
                
                # Check disability columns A through E
                disability_text = " ".join([row.get(f"Category of Disabilities - {col}", "") for col in "ABCDE"]).lower()
                if disability in disability_text: score += 10
                
                scored_jobs.append({"score": score, "title": row.get("Designation", "Job"), "dept": row.get("Department", "")})
    except: pass
    
    scored_jobs.sort(key=lambda x: x["score"], reverse=True)
    out = "### Your Top Matches:\n\n"
    for i, job in enumerate(scored_jobs[:3], 1):
        out += f"**{i}. {job['title']}**\n*Dept: {job['dept']}*\n\n"
    return out

@app.post("/api/chat")
async def chat_endpoint(payload: ChatPayload):
    msg_orig = payload.user_message.strip()
    msg_low = msg_orig.lower()
    email = payload.email.strip().lower()
    step = payload.current_step

    if step == "get_email":
        otp = str(random.randint(1000, 9999))
        OTP_STORE[email] = otp
        send_otp_via_email(email, otp)
        return {"status": "success", "ai_response": "Code sent! Check your email.", "next_step": "verify_code"}

    elif step == "verify_code":
        if OTP_STORE.get(email) == msg_low:
            del OTP_STORE[email]
            return {"status": "success", "ai_response": "Login success! Introduce yourself (Name & Dept).", "next_step": "get_intro"}
        return {"status": "error", "ai_response": "Wrong code.", "next_step": "verify_code"}

    elif step == "get_intro":
        data = extract_info_with_gemini(msg_orig)
        USER_SESSIONS[email] = {"Email": email, "Name": data["name"], "Department": data["department"]}
        return {"status": "success", "ai_response": f"Hi {data['name']}! Interest in {data['department']} noted. Qualification?", "next_step": "get_qualification"}

    elif step == "get_qualification":
        USER_SESSIONS[email]["Qualification"] = msg_orig
        return {"status": "success", "ai_response": "Disability type?", "next_step": "get_disability"}

    elif step == "get_disability":
        USER_SESSIONS[email]["Primary Disability"] = msg_orig
        return {"status": "success", "ai_response": "Functional strengths?", "next_step": "get_functional"}

    elif step == "get_functional":
        profile = USER_SESSIONS[email]
        profile["Functional Strengths"] = msg_orig
        
        # Save to CSV
        with open('user_database.csv', 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["Email", "Name", "Department", "Qualification", "Primary Disability", "Functional Strengths"])
            if f.tell() == 0: writer.writeheader()
            writer.writerow(profile)
            
        return {"status": "success", "ai_response": find_top_jobs(profile), "next_step": "finished"}

    return {"status": "error", "ai_response": "I'm lost.", "next_step": "get_email"}
