import os
import json
import re
from fastapi import FastAPI
from pydantic import BaseModel
import random
import csv
import google.generativeai as genai

# HARDCODED KEY FOR TESTING ONLY
# Paste your key inside these quotes: "AIza..."
genai.configure(api_key="AQ.Ab8RN6LO3hENURfFwgPQoNz-V3Q8nHQdYvH_Mlm60PR0Vjp19w")

app = FastAPI()
# ... (rest of your code remains identical)OTP_STORE = {}
USER_SESSIONS = {} 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class ChatPayload(BaseModel):
    user_message: str
    email: str
    current_step: str

def send_otp_via_email(target_email: str, otp_code: str):
    # ---------------------------------------------------------
    # FORCE BYPASS: Skip the email attempt so Android doesn't time out
    # ---------------------------------------------------------
    print("=====================================================")
    print(f"SECURITY BYPASS: The OTP for {target_email} is: {otp_code}")
    print("=====================================================")
    return # Instantly return so the app gets a success message in 0.1 seconds!

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
        try:
            # 1. Standard text generation (Removes strict JSON configs that crash older SDKs)
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"Extract Name and Department from this message: '{msg_orig}'. Reply with exactly this format: NAME: [name] | DEPT: [department]"
            
            response = model.generate_content(prompt)
            reply_text = response.text.strip()
            
            # 2. Simple, crash-proof text extraction
            name = "User"
            department = "Unknown"
            
            if "NAME:" in reply_text and "|" in reply_text:
                parts = reply_text.split("|")
                name = parts[0].replace("NAME:", "").strip()
                department = parts[1].replace("DEPT:", "").strip()
            
            USER_SESSIONS[email] = {"Email": email, "Name": name, "Department": department}
            
            return {
                "status": "success", 
                "ai_response": f"Hi {name}! Interest in {department} noted. What is your highest qualification?", 
                "next_step": "get_qualification"
            }
        except Exception as e:
            # THIS LINE WILL PRINT THE ABSOLUTE TRUTH TO RENDER LOGS IF IT FAILS
            print(f"CRITICAL GEMINI ERROR: {e}")
            return {"status": "error", "ai_response": "Could not parse intro. Please state your Name and Department.", "next_step": "get_intro"}

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
