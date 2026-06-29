import os
import smtplib
from email.mime.text import MIMEText
from fastapi import FastAPI
from pydantic import BaseModel
import difflib
import random

app = FastAPI()

# In-memory dictionary to temporarily store OTPs (e.g., {"janani@example.com": "5821"})
OTP_STORE = {}

class ChatPayload(BaseModel):
    user_message: str
    email: str
    current_step: str

# ==========================================
# GMAIL SMTP FUNCTION
# ==========================================
def send_otp_via_email(target_email: str, otp_code: str):
    # 1. Your Credentials
    sender_email = "janarajan04@gmail.com" 
    
    # 2. Securely fetch the password from Environment Variables
    app_password = os.getenv("GMAIL_APP_PASSWORD")
    
    # 3. Build the Email
    msg = MIMEText(f"Welcome to Suyog+!\n\nYour verification code is: {otp_code}")
    msg['Subject'] = "Suyog+ Verification Code"
    msg['From'] = sender_email
    msg['To'] = target_email
    
    # 4. Connect to Gmail and Send
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls() # Secure the connection
        server.login(sender_email, app_password)
        server.send_message(msg)
        server.quit()
        print(f"DEBUG: Successfully sent OTP {otp_code} to {target_email}")
    except Exception as e:
        print(f"DEBUG: Failed to send email. Error: {e}")


@app.post("/api/chat")
async def chat_endpoint(payload: ChatPayload):
    msg = payload.user_message.strip().lower()
    email = payload.email.strip().lower()
    step = payload.current_step

    # -----------------------------------------
    # STEP A1: Login (get_email)
    # -----------------------------------------
    if step == "get_email":
        if "@" in msg and "." in msg:
            # 1. Generate a random 4-digit OTP
            generated_otp = str(random.randint(1000, 9999))
            
            # 2. Save it in our temporary dictionary linked to their email
            OTP_STORE[email] = generated_otp 
            
            # 3. Call your custom API function to send the email
            send_otp_via_email(email, generated_otp)
            
            return {
                "status": "success",
                "ai_response": f"We've sent a verification code to {email}. Please check your inbox and enter the 4-digit code.",
                "next_step": "verify_code"
            }
        else:
            return {
                "status": "error",
                "ai_response": "Please enter a valid email address.",
                "next_step": "get_email"
            }

    # -----------------------------------------
    # STEP A2: Verify OTP (verify_code)
    # -----------------------------------------
    elif step == "verify_code":
        # Look up the OTP we saved for this specific email
        saved_otp = OTP_STORE.get(email)
        
        if saved_otp and msg == saved_otp: 
            # Success! Delete the OTP from memory so it can't be reused
            del OTP_STORE[email] 
            
            return {
                "status": "success",
                "ai_response": "Login successful! Please introduce yourself (e.g., 'I'm Janani and I love Administration').",
                "next_step": "get_intro"
            }
        else:
            return {
                "status": "error",
                "ai_response": "Incorrect code. Please try again.",
                "next_step": "verify_code"
            }

    # -----------------------------------------
    # STEP B: The Brain (get_intro)
    # -----------------------------------------
    elif step == "get_intro":
        UNIQUE_DEPTS = ["administration", "it", "hr", "finance"] 
        return {
            "status": "success",
            "ai_response": "Nice to meet you! You selected Administration. What is your highest educational qualification?",
            "next_step": "get_qualification"
        }

    # -----------------------------------------
    # STEP C: Qualification (get_qualification)
    # -----------------------------------------
    elif step == "get_qualification":
        return {
            "status": "success",
            "ai_response": "Got it. What is your primary disability? (e.g., Visual, Physical, Intellectual, Hearing)",
            "next_step": "get_disability"
        }

    # -----------------------------------------
    # STEP D: Disability & Sub-category (get_disability)
    # -----------------------------------------
    elif step == "get_disability":
        if "intellectual" in msg:
            return {
                "status": "success",
                "ai_response": "Since you selected Intellectual, could you specify the sub-category? (e.g., Autism, Dyslexia, Down Syndrome)",
                "next_step": "get_intellectual_sub"
            }
        else:
            return {
                "status": "success",
                "ai_response": "Thank you. Now, what are your functional strengths?",
                "next_step": "get_functional"
            }

    # -----------------------------------------
    # STEP D2: Intellectual Sub-category (get_intellectual_sub)
    # -----------------------------------------
    elif step == "get_intellectual_sub":
        return {
            "status": "success",
            "ai_response": "Thank you. Now, what are your functional strengths?",
            "next_step": "get_functional"
        }

    # -----------------------------------------
    # STEP E: Saving & Searching (get_functional)
    # -----------------------------------------
    elif step == "get_functional":
        markdown_jobs = "### Top 3 Jobs\n1. Admin Assistant...\n2. Data Entry...\n3. Receptionist..."
        return {
            "status": "success",
            "ai_response": f"Profile saved! Here are your matches:\n{markdown_jobs}",
            "next_step": "finished" 
        }

    return {"status": "error", "ai_response": "I'm lost.", "next_step": "get_email"}
