# core_logic.py
from google import genai
import os
from dotenv import load_dotenv

# This tells Python to look specifically for 'secret.env' instead of the default '.env'
load_dotenv("secret.env")

# Now os.environ can find your key perfectly
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def process_suyog_data(user_input: str) -> dict:
    """
    Takes the user's input, sends it to Gemini, and returns the AI's response.
    """
    try:
        # Construct the prompt instructing Gemini how to act for your Job Finder
        system_prompt = "You are a helpful bilingual career assistant. "
        full_prompt = f"{system_prompt}\nUser request: {user_input}"
        
        # Call the Gemini API
        response = client.models.generate_content(
            model="gemini-3.5-flash",
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
