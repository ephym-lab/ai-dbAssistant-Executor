import os
import json
import sys
from dotenv import load_dotenv
from config import SYSTEM_PROMPT
from services import AIServiceFactory

# Load environment variables
load_dotenv()

def main():
    print("AI SQL Assistant Initialized.")
    
    # Initialize Service
    try:
        ai_service = AIServiceFactory.get_service()
        print(f"Using AI Service: {ai_service.__class__.__name__}")
    except Exception as e:
        print(f"Failed to initialize AI Service: {e}")
        return

    print("Type 'exit' or 'quit' to stop.")
    
    while True:
        try:
            user_input = input("\n> ")
            if user_input.lower() in ["exit", "quit"]:
                break
            
            if not user_input.strip():
                continue

            response_str = ai_service.get_response(user_input, SYSTEM_PROMPT)
            
            try:
                # parse json to ensure valid format
                # Some LLMs might wrap json in markdown code blocks like ```json ... ```
                clean_str = response_str
                if "```" in clean_str:
                     clean_str = clean_str.replace("```json", "").replace("```", "").strip()

                response_json = json.loads(clean_str)
                print("\n[Assistant Explanation]:", response_json.get("content"))
                if response_json.get("query"):
                    print("[Generated SQL]:", response_json.get("query"))
            except json.JSONDecodeError:
                print("\n[Raw Response (Invalid JSON)]:", response_str)
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break

if __name__ == "__main__":
    main()
