# core_logic.py
from google import genai
import os
from dotenv import load_dotenv

# This tells Python to look specifically for 'secret.env' instead of the default '.env'
load_dotenv("secret.env")

# Now os.environ can find your key perfectly
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# In your core_logic.py file

# In your core_logic.py file

def process_suyog_data(user_input: str) -> dict:
    try:
        # UPDATED: Specialized for inclusive job searching
        system_prompt = """
        You are an empathetic and expert Job Finder Assistant dedicated to helping persons with disabilities 
        find inclusive and accessible job opportunities.
        
        Guidelines:
        1. When helping a user, ask about their specific qualifications, skills, and any specific accessibility 
           requirements they need in a workplace.
        2. Provide advice on identifying inclusive employers, companies with strong DE&I (Diversity, Equity, and Inclusion) 
           policies, and roles that support remote or flexible work arrangements.
        3. Use encouraging, respectful, and professional language.
        4. Focus on matching the user's specific skills to potential roles. 
        5. If the user mentions a specific disability or accessibility need, provide information on 
           workplace accommodations and how to navigate those discussions professionally.
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
