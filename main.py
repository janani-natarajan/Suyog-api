import os
import json
import smtplib
from email.mime.text import MIMEText
from fastapi import FastAPI
from pydantic import BaseModel
import random
import csv

import google.generativeai as genai

# Securely load the API key from environment variables
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
        print(f"DEBUG: Successfully sent OTP {otp_code} to {target_email}")
    except Exception as e:
        print(f"DEBUG: Failed to send email. Error: {e}")

def extract_info_with_gemini(text: str):
    """Uses Gemini to extract the name and department from a natural sentence."""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Extract the user's name and their preferred department from this text: "{text}"
        The department must be one of these exactly: Administration, IT, HR, Finance, Accounts, Postal.
        Return ONLY a raw JSON object in this exact format: {{"name": "extracted_name", "department": "extracted_department"}}
        If you cannot find a valid department, use "Unknown".
        Do not use markdown formatting.
        """
        response = model.generate_content(prompt)
        cleaned_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(cleaned_text)
    except Exception as e:
        print(f"Gemini Error: {e}")
        return {"name": "User", "department": "Unknown"}

# --- 3. NEW DATABASE MATCHING ENGINE ---
def find_top_jobs(user_profile: dict):
    """Scans jobs.csv and scores matches based on department and disability."""
    user_dept = user_profile.get("Department", "").lower()
    primary_disability = user_profile.get("Primary Disability", "").lower()
    sub_category = user_profile.get("Sub-Category", "").lower()
    
    scored_jobs = []
    
    try:
        # Open your uploaded jobs.csv
        with open('jobs.csv', mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                score = 0
                job_dept = row.get("Department", "").lower()
                job_title = row.get("Designation", "").lower()
                
                # Point system for Department
                if user_dept and (user_dept in job_dept or user_dept in job_title):
                    score += 5
                    
                # Combine all disability columns to search them at once
                disability_text = " ".join([
                    row.get("Category of Disabilities - A", ""),
                    row.get("Category of Disabilities - B", ""),
                    row.get("Category of Disabilities - C", ""),
                    row.get("Category of Disabilities - D", ""),
                    row.get("Category of Disabilities - E", "")
                ]).lower()
                
                # Point system for Accommodations
                if primary_disability and primary_disability in disability_text:
                    score += 10
                if sub_category != "n/a" and sub_category in disability_text:
                    score += 10
                
                # Add to list even if score is 0, so we always have fallbacks
                scored_jobs.append({
                    "score": score,
                    "title": row.get("Designation", "Unknown Job").strip(),
                    "department": row.get("Department", "Various").strip()
                })
                
    except Exception as e:
        print(f"Error reading jobs.csv: {e}")
        return "### Top 3 Jobs\n1. Admin Assistant\n2. Data Entry Clerk\n3. Front Desk Receptionist"

    # Sort the jobs from highest score to lowest
    scored_jobs.sort(key=lambda x: x["score"], reverse=True)
    
    # Grab the top 3 and format them into Markdown for the Android App
    top_3 = scored_jobs[:3]
    markdown_output = "### Your Top Matches:\n\n"
    for i, job in enumerate(top_3, 1):
        markdown_output += f"**{i}. {job['title']}**\n*Department: {job['department']}*\n\n"
        
    return markdown_output


@app.post("/api/chat")
async def chat_endpoint(payload: ChatPayload):
    msg_original = payload.user_message.strip()
    msg_lower = msg_original.lower()
    email = payload.email.strip().lower()
    step = payload.current_step

    # -----------------------------------------
    # STEP A1 & A2: Login & Verification
    # -----------------------------------------
    if step == "get_email":
        if "@" in msg_lower and "." in msg_lower:
            generated_otp = str(random.randint(1000, 9999))
            OTP_STORE[email] = generated_otp 
            send_otp_via_email(email, generated_otp)
            return {"status": "success", "ai_response": f"We've sent a verification code to {email}. Please check your inbox.", "next_step": "verify_code"}
        return {"status": "error", "ai_response": "Please enter a valid email address.", "next_step": "get_email"}

    elif step == "verify_code":
        saved_otp = OTP_STORE.get(email)
        if saved_otp and msg_lower == saved_otp: 
            del OTP_STORE[email] 
            return {"status": "success", "ai_response": "Login successful! Please introduce yourself (e.g., 'I am Janani and I love Administration').", "next_step": "get_intro"}
        return {"status": "error", "ai_response": "Incorrect code. Please try again.", "next_step": "verify_code"}

    # -----------------------------------------
    # STEP B: The Brain (get_intro)
    # -----------------------------------------
    elif step == "get_intro":
        extracted_data = extract_info_with_gemini(msg_original)
        user_name = extracted_data.get("name", "there")
        user_dept = extracted_data.get("department", "Unknown")
        
        # Added a few more departments based on your CSV sample!
        UNIQUE_DEPTS = ["administration", "it", "hr", "finance", "accounts", "postal"] 
        
        if user_dept.lower() in UNIQUE_DEPTS:
            USER_SESSIONS[email] = {"Email": email, "Name": user_name, "Department": user_dept.capitalize()}
            return {"status": "success", "ai_response": f"Nice to meet you, {user_name}! I see you are interested in {user_dept.capitalize()}. What is your highest educational qualification?", "next_step": "get_qualification"}
        else:
            return {"status": "error", "ai_response": f"Nice to meet you, {user_name}! I didn't quite catch your preferred field. Please choose from: Administration, IT, HR, Finance, Accounts, or Postal.", "next_step": "get_intro" }

    # -----------------------------------------
    # STEP C: Qualification 
    # -----------------------------------------
    elif step == "get_qualification":
        if email not in USER_SESSIONS: USER_SESSIONS[email] = {}
        USER_SESSIONS[email]["Qualification"] = msg_original
        return {"status": "success", "ai_response": "Got it. What is your primary disability? (e.g., Visual, Physical, Intellectual, Hearing)", "next_step": "get_disability"}

    # -----------------------------------------
    # STEP D: Disability & Sub-category
    # -----------------------------------------
    elif step == "get_disability":
        if email not in USER_SESSIONS: USER_SESSIONS[email] = {}
        USER_SESSIONS[email]["Primary Disability"] = msg_original
        
        if "intellectual" in msg_lower:
            return {"status": "success", "ai_response": "Since you selected Intellectual, could you specify the sub-category? (e.g., Autism, Dyslexia, Down Syndrome)", "next_step": "get_intellectual_sub"}
        else:
            USER_SESSIONS[email]["Sub-Category"] = "N/A"
            return {"status": "success", "ai_response": "Thank you. Now, what are your functional strengths?", "next_step": "get_functional"}

    elif step == "get_intellectual_sub":
        if email not in USER_SESSIONS: USER_SESSIONS[email] = {}
        USER_SESSIONS[email]["Sub-Category"] = msg_original
        return {"status": "success", "ai_response": "Thank you. Now, what are your functional strengths?", "next_step": "get_functional"}

    # -----------------------------------------
    # STEP E: Saving & Searching 
    # -----------------------------------------
    elif step == "get_functional":
        if email not in USER_SESSIONS: USER_SESSIONS[email] = {}
        USER_SESSIONS[email]["Functional Strengths"] = msg_original
        
        user_profile = USER_SESSIONS.get(email, {})
        
        # 1. PERMANENTLY SAVE TO user_database.csv
        file_exists = os.path.isfile('user_database.csv')
        with open('user_database.csv', mode='a', newline='', encoding='utf-8') as file:
            fieldnames = ["Email", "Name", "Department", "Qualification", "Primary Disability", "Sub-Category", "Functional Strengths"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            clean_profile = {k: user_profile.get(k, "N/A") for k in fieldnames}
            writer.writerow(clean_profile)

        # 2. TRIGGER THE MATCHING ENGINE
        markdown_jobs = find_top_jobs(user_profile)
        
        # 3. CLEAR SHORT-TERM MEMORY
        if email in USER_SESSIONS:
            del USER_SESSIONS[email]
            
        return {
            "status": "success",
            "ai_response": f"Profile saved successfully! {markdown_jobs}",
            "next_step": "finished" 
        }

    return {"status": "error", "ai_response": "I'm lost.", "next_step": "get_email"}
