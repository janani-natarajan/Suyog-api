# core_logic.py
from google import genai
import os
from dotenv import load_dotenv

# This tells Python to look specifically for 'secret.env' instead of the default '.env'
load_dotenv("secret.env")

# Now os.environ can find your key perfectly
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# In your core_logic.py file

def process_suyog_data(user_input: str) -> dict:
    """
    Takes the user's input, sends it to Gemini, and returns the AI's response.
    """
    try:
        # UPDATED: Persona changed to a specialized Job Finder Assistant
        system_prompt = """
        You are an expert Job Finder Assistant. 
        Your goal is to help users find jobs based on their skills, location, and experience.
        
        Guidelines:
        1. If the user hasn't provided their target role, location, or experience level, ask for them politely.
        2. Provide actionable advice: suggest specific job platforms, keyword search strategies, or relevant skill-based certifications.
        3. Keep your tone professional, encouraging, and concise.
        4. Do not provide general career counseling or non-job-related advice.
        """
        
        full_prompt = f"{system_prompt}\nUser request: {user_input}"
        
        # NOTE: Ensure you are using a supported model name like 'gemini-1.5-flash'
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=full_prompt
        )
        
        return {
            "status": "success",
            "ai_response": response.text
        }
    except Exception as e:
         return {
            "status": "error",
            "ai_response": str(e)
        }
