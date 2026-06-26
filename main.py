# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from core_logic import process_suyog_data

app = FastAPI(title="Suyog Gemini API")

class ChatPayload(BaseModel):
    user_message: str

@app.post("/api/chat")
def handle_chat(payload: ChatPayload):
    # Pass the user's message to your Gemini function
    result = process_suyog_data(user_input=payload.user_message)
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["ai_response"])
        
    return result
