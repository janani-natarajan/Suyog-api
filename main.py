import os
import json
import smtplib
from email.mime.text import MIMEText
from fastapi import FastAPI
from pydantic import BaseModel
import random
import csv # --- NEW: Import CSV module ---

# --- 1. NEW GEMINI IMPORTS & SETUP ---
import google.generativeai as genai

# Securely load the API key from environment variables
gemini_key = os.getenv("GEMINI_API_KEY")
if gemini_key:
    genai.configure(api_key=gemini_key)

app = FastAPI()

OTP_STORE = {}
USER_SESSIONS = {} # --- NEW: Short-term memory for active chats ---

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

# --- 2. NEW GEMINI HELPER FUNCTION ---
def extract_info_with_gemini(text: str):
    """Uses Gemini to extract the name and department from a natural sentence."""
    try:
        # Use the fast and lightweight flash model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Strict instructions so Gemini only returns code we can use
        prompt = f"""
        Extract the user's name and their preferred department from this text: "{text}"
        The department must be one of these exactly: Administration, IT, HR, Finance.
        Return ONLY a raw JSON object in this exact format: {{"name": "extracted_name", "department": "extracted_department"}}
        If you cannot find a valid department, use "Unknown".
        Do not use markdown formatting.
        """
        
        response = model.generate_content(prompt)
        
        # Clean up the text and turn it into a Python dictionary
        cleaned_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(cleaned_text)
        
    except Exception as e:
        print(f"Gemini Error: {e}")
        return {"name": "User", "department": "Unknown"}

@app.post("/api/chat")
async def chat_endpoint(payload: ChatPayload):
    # We keep the original case for Gemini to extract names properly, 
    # but use lowercase for simple matching later.
    msg_original = payload.user_message.strip()
    msg_lower = msg_original.lower()
    
    email = payload.email.strip().lower()
    step = payload.current_step

    # -----------------------------------------
    # STEP A1: Login
    # -----------------------------------------
    if step == "get_email":
        if "@" in msg_lower and "." in msg_lower:
            generated_otp = str(random.randint(1000, 9999))
            OTP_STORE[email] = generated_otp 
            send_otp_via_email(email, generated_otp)
            return {
                "status": "success",
                "ai_response": f"We've sent a verification code to {email}. Please check your inbox and enter the 4-digit code.",
                "next_step": "verify_code"
            }
        else:
            return {"status": "error", "ai_response": "Please enter a valid email address.", "next_step": "get_email"}

    # -----------------------------------------
    # STEP A2: Verify OTP
    # -----------------------------------------
    elif step == "verify_code":
        saved_otp = OTP_STORE.get(email)
        if saved_otp and msg_lower == saved_otp: 
            del OTP_STORE[email] 
            return {
                "status": "success",
                "ai_response": "Login successful! Please introduce yourself (e.g., 'I am Janani and I love Administration').",
                "next_step": "get_intro"
            }
        else:
            return {"status": "error", "ai_response": "Incorrect code. Please try again.", "next_step": "verify_code"}

    # -----------------------------------------
    # STEP B: The Brain (get_intro) - UPGRADED
    # -----------------------------------------
    elif step == "get_intro":
        # 1. Ask Gemini to read the user's mind!
        extracted_data = extract_info_with_gemini(msg_original)
        user_name = extracted_data.get("name", "there")
        user_dept = extracted_data.get("department", "Unknown")
        
        UNIQUE_DEPTS = ["administration", "it", "hr", "finance"] 
        
        # 2. Check if Gemini found a valid department
        if user_dept.lower() in UNIQUE_DEPTS:
            
            # --- START MEMORY TRACKING ---
            USER_SESSIONS[email] = {
                "Email": email,
                "Name": user_name,
                "Department": user_dept.capitalize()
            }
            
            return {
                "status": "success",
                "ai_response": f"Nice to meet you, {user_name}! I see you are interested in {user_dept.capitalize()}. What is your highest educational qualification?",
                "next_step": "get_qualification"
            }
        else:
            # If they just said "Hi I am Janani", ask them to clarify the department
            return {
                "status": "error",
                "ai_response": f"Nice to meet you, {user_name}! I didn't quite catch your preferred field. Please choose from: Administration, IT, HR, or Finance.",
                "next_step": "get_intro" 
            }

    # -----------------------------------------
    # STEP C: Qualification 
    # -----------------------------------------
    elif step == "get_qualification":
        if email not in USER_SESSIONS: USER_SESSIONS[email] = {}
        USER_SESSIONS[email]["Qualification"] = msg_original
        
        return {
            "status": "success",
            "ai_response": "Got it. What is your primary disability? (e.g., Visual, Physical, Intellectual, Hearing)",
            "next_step": "get_disability"
        }

    # -----------------------------------------
    # STEP D: Disability & Sub-category
    # -----------------------------------------
    elif step == "get_disability":
        if email not in USER_SESSIONS: USER_SESSIONS[email] = {}
        USER_SESSIONS[email]["Primary Disability"] = msg_original
        
        if "intellectual" in msg_lower:
            return {
                "status": "success",
                "ai_response": "Since you selected Intellectual, could you specify the sub-category? (e.g., Autism, Dyslexia, Down Syndrome)",
                "next_step": "get_intellectual_sub"
            }
        else:
            USER_SESSIONS[email]["Sub-Category"] = "N/A"
            return {
                "status": "success",
                "ai_response": "Thank you. Now, what are your functional strengths?",
                "next_step": "get_functional"
            }

    # -----------------------------------------
    # STEP D2: Intellectual Sub-category
    # -----------------------------------------
    elif step == "get_intellectual_sub":
        if email not in USER_SESSIONS: USER_SESSIONS[email] = {}
        USER_SESSIONS[email]["Sub-Category"] = msg_original
        
        return {
            "status": "success",
            "ai_response": "Thank you. Now, what are your functional strengths?",
            "next_step": "get_functional"
        }

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
            
            # Use dictionary comprehension to ensure we only write keys that exist in fieldnames
            clean_profile = {k: user_profile.get(k, "N/A") for k in fieldnames}
            writer.writerow(clean_profile)

        # 2. MATCH WITH jobs.csv (Placeholder logic for now)
        # TODO: Search jobs.csv
        markdown_jobs = "### Top Matches Retrieved\n1. Admin Assistant\n2. Data Entry Clerk\n3. Front Desk Receptionist"
        
        # 3. CLEAR SHORT-TERM MEMORY
        if email in USER_SESSIONS:
            del USER_SESSIONS[email]
            
        return {
            "status": "success",
            "ai_response": f"Profile saved successfully! Here are your matches:\n{markdown_jobs}",
            "next_step": "finished" 
        }

    return {"status": "error", "ai_response": "I'm lost.", "next_step": "get_email"}
