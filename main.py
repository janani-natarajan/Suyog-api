from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import os
from core_logic import process_suyog_data # Ensure this is your logic file

app = FastAPI(title="Suyog Gemini API")

class ChatPayload(BaseModel):
    user_message: str

# Cache the dataframe so it loads only once at startup
@app.on_event("startup")
def load_data():
    global df
    if os.path.exists('jobs.csv'):
        df = pd.read_csv('jobs.csv')
    else:
        df = pd.DataFrame()

@app.post("/api/chat")
def handle_chat(payload: ChatPayload):
    # 1. Perform the CSV lookup/context retrieval
    user_msg = payload.user_message.lower()
    
    # Simple search logic
    matches = df[
        df['Department'].astype(str).str.contains(user_msg, case=False, na=False) | 
        df['Job Title'].astype(str).str.contains(user_msg, case=False, na=False)
    ]
    
    # 2. Get the context string
    context = matches.head(3).to_string(index=False) if not matches.empty else "No matching jobs found."
    
    # 3. Pass the user message AND the retrieved CSV context to your logic
    result = process_suyog_data(user_input=payload.user_message, csv_context=context)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("ai_response", "Unknown error"))
        
    return result
