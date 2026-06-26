from google import genai
import os
from dotenv import load_dotenv

load_dotenv("secret.env")
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def process_suyog_data(user_input: str, csv_context: str) -> dict:
    try:
        # The system prompt now incorporates the retrieved CSV data
        system_prompt = f"""
        You are an empathetic and expert Job Finder Assistant dedicated to helping persons with disabilities 
        find inclusive and accessible job opportunities.
        
        CRITICAL: Use the following database information to answer the user request:
        ---
        {csv_context}
        ---
        
        Guidelines:
        1. Only suggest jobs found in the provided database information above.
        2. Ask about their specific qualifications, skills, and any specific accessibility requirements.
        3. Provide advice on identifying inclusive employers.
        4. If no relevant job is found in the database context, politely state that.
        5. Maintain an encouraging, respectful, and professional tone.
        """
        
        full_prompt = f"{system_prompt}\nUser request: {user_input}"
        
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
