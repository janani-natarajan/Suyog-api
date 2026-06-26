from pydantic import BaseModel
import difflib

# 1. Update the Pydantic Model to match Android
class ChatPayload(BaseModel):
    user_message: str
    mobile: str
    current_step: str

# 2. Update your endpoint to act as the State Machine
@app.post("/api/chat")
async def chat_endpoint(payload: ChatPayload):
    msg = payload.user_message.strip()
    step = payload.current_step
    mobile = payload.mobile

    # -----------------------------------------
    # STEP A: Login (get_mobile)
    # -----------------------------------------
    if step == "get_mobile":
        if len(msg) == 10 and msg.isdigit():
            # Check your user_database.csv here!
            # If new user:
            return {
                "status": "success",
                "ai_response": "Welcome! Please introduce yourself (e.g., 'I'm Janani and I love Administration').",
                "next_step": "get_intro" # Move to Step B
            }
        else:
            return {
                "status": "error",
                "ai_response": "Please enter a valid 10-digit mobile number.",
                "next_step": "get_mobile" # Keep them stuck here until they get it right
            }

    # -----------------------------------------
    # STEP B: The Brain (get_intro)
    # -----------------------------------------
    elif step == "get_intro":
        # 1. Send 'msg' to Gemini to extract Name and Department
        # gemini_extracted_dept = ask_gemini(msg) 
        
        # 2. Fuzzy Logic check
        UNIQUE_DEPTS = ["Administration", "IT", "HR", "Finance"] # Example
        # match = difflib.get_close_matches(gemini_extracted_dept, UNIQUE_DEPTS, n=1, cutoff=0.6)
        
        # if match:
        return {
            "status": "success",
            "ai_response": f"Nice to meet you! You selected Administration. Do you have a disability?",
            "next_step": "get_disability" # Move to Step C
        }
        # else: force them to try again

    # -----------------------------------------
    # STEP C: Data Collection (get_disability)
    # -----------------------------------------
    elif step == "get_disability":
        # Save disability info
        return {
            "status": "success",
            "ai_response": "What is your qualification?",
            "next_step": "get_qualification"
        }

    # -----------------------------------------
    # STEP D: Saving & Searching
    # -----------------------------------------
    elif step == "get_qualification":
        # 1. Save all data to user_database.csv using 'mobile' as the ID
        # 2. Filter jobs.csv based on the collected data
        # 3. Format Top 3 jobs in Markdown
        
        markdown_jobs = "### Top 3 Jobs\n1. Admin Assistant...\n2. Data Entry...\n3. Receptionist..."
        
        return {
            "status": "success",
            "ai_response": f"Profile saved! Here are your matches:\n{markdown_jobs}",
            "next_step": "finished" 
        }

    # Default fallback
    return {"status": "error", "ai_response": "I'm lost.", "next_step": "get_mobile"}
