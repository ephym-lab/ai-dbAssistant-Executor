import os
import json
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from config import SYSTEM_PROMPT
from services import AIServiceFactory
from schemas import QuestionRequest, SQLResponse

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="AI SQL Assistant API",
    description="Convert natural language to SQL queries",
    version="1.0.0"
)

# Initialize AI Service
ai_service = AIServiceFactory.get_service()


@app.get("/")
def read_root():
    return {
        "message": "AI SQL Assistant API",
        "service": ai_service.__class__.__name__,
        "endpoints": {
            "POST /generate-sql": "Generate SQL from natural language"
        }
    }

@app.post("/generate-sql", response_model=SQLResponse)
def generate_sql(request: QuestionRequest):
    """
    Generate SQL query from natural language question.
    
    - **question**: Natural language question
    - **db_schema**: Optional database schema context
    """
    try:
        # Enhance prompt with schema if provided
        user_input = request.question
        if request.db_schema:
            user_input = f"Database Schema:\n{request.db_schema}\n\nUser Question: {request.question}"
        
        # Get response from AI service
        response_str = ai_service.get_response(user_input, SYSTEM_PROMPT)
        
        # Clean and parse JSON response
        clean_str = response_str
        if "```" in clean_str:
            clean_str = clean_str.replace("```json", "").replace("```", "").strip()
        
        try:
            response_json = json.loads(clean_str)
            return SQLResponse(
                content=response_json.get("content", ""),
                query=response_json.get("query", "")
            )
        except json.JSONDecodeError:
            # If response is not valid JSON, return it as content
            return SQLResponse(
                content=f"Error parsing response: {response_str}",
                query=""
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": ai_service.__class__.__name__
    }
