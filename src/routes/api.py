import os
import json
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from config import SYSTEM_PROMPT
from services import AIServiceFactory, DBExecutorFactory, QueryValidator
from schemas import QuestionRequest, SQLResponse, ExecuteRequest, ExecuteResponse, DBInfoResponse, ConnectRequest

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

# Global database executor (managed connection)
db_executor = None


@app.get("/")
def read_root():
    return {
        "message": "AI SQL Assistant API",
        "service": ai_service.__class__.__name__,
        "endpoints": {
            "POST /generate-sql": "Generate SQL from natural language",
            "POST /execute-sql": "Execute SQL query",
            "POST /validate-sql": "Validate SQL query (dry-run)",
            "GET /db-info": "Database connection information",
            "POST /connect-db": "Connect to database",
            "POST /disconnect-db": "Disconnect from database"
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

@app.post("/execute-sql", response_model=ExecuteResponse)
def execute_sql(request: ExecuteRequest):
    """
    Execute a SQL query against the configured database.
    
    - **query**: SQL query to execute
    - **dry_run**: If true, validates query without executing 
    """
    global db_executor
    
    try:
        # Get configuration
        allow_write = os.getenv("ALLOW_WRITE_OPERATIONS", "false").lower() == "true"
        allow_ddl = os.getenv("ALLOW_DDL_OPERATIONS", "false").lower() == "true"
        max_rows = int(os.getenv("MAX_ROWS_RETURNED", 1000))
        
        # Validate query
        is_valid, error_msg = QueryValidator.validate_query(
            request.query,
            allow_write=allow_write,
            allow_ddl=allow_ddl
        )
        
        if not is_valid:
            raise HTTPException(status_code=403, detail=error_msg)
        
        # Add LIMIT if needed for SELECT queries
        query = QueryValidator.add_limit_if_needed(request.query, max_rows)
        
        # Use global executor if available, otherwise create temporary one
        use_global = db_executor and db_executor.connection
        
        if use_global:
            executor = db_executor
        else:
            # Get temporary executor
            executor = DBExecutorFactory.get_executor()
            if not executor:
                raise HTTPException(
                    status_code=500,
                    detail="Database not configured. Set DB_TYPE environment variable."
                )
        
        # Execute query
        result = executor.execute_query(query, dry_run=request.dry_run)
        
        # Only disconnect if using temporary connection
        if not use_global:
            executor.disconnect()
        
        return ExecuteResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/validate-sql", response_model=ExecuteResponse)
def validate_sql(request: ExecuteRequest):
    """
    Validate SQL query without executing (dry-run mode).
    
    - **query**: SQL query to validate
    """
    request.dry_run = True
    return execute_sql(request)

@app.get("/db-info", response_model=DBInfoResponse)
def get_db_info():
    """
    Get database connection information.
    """
    global db_executor
    
    try:
        # Use global executor if available
        if db_executor:
            info = db_executor.get_connection_info()
            return DBInfoResponse(**info)
        
        # Otherwise create temporary executor to get info
        executor = DBExecutorFactory.get_executor()
        if not executor:
            raise HTTPException(
                status_code=500,
                detail="Database not configured. Set DB_TYPE environment variable."
            )
        
        info = executor.get_connection_info()
        return DBInfoResponse(**info)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/connect-db")
def connect_database(request: ConnectRequest):
    """
    Establish a persistent connection to the database using a connection string.
    
    - **db_type**: Database type ("postgresql" or "mysql")
    - **connection_string**: Database connection string (e.g., postgresql://user:pass@host:port/db)
    """
    global db_executor
    
    try:
        # Check if already connected
        if db_executor and db_executor.connection:
            return {
                "success": True,
                "message": "Database already connected. Disconnect first to connect to a different database.",
                "connection_info": db_executor.get_connection_info()
            }
        
        # Create executor from connection string with db_type
        db_executor = DBExecutorFactory.from_connection_string(
            db_type=request.db_type,
            connection_string=request.connection_string
        )
        if not db_executor:
            raise HTTPException(
                status_code=400,
                detail="Failed to create database executor from connection string."
            )
        
        # Connect
        db_executor.connect()
        
        return {
            "success": True,
            "message": "Database connected successfully",
            "connection_info": db_executor.get_connection_info()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/disconnect-db")
def disconnect_database():
    """
    Disconnect from the database.
    """
    global db_executor
    
    try:
        # Check if connected
        if not db_executor or not db_executor.connection:
            return {
                "success": True,
                "message": "Database already disconnected"
            }
        
        # Get connection info before disconnecting
        connection_info = db_executor.get_connection_info()
        
        # Disconnect
        db_executor.disconnect()
        db_executor = None
        
        return {
            "success": True,
            "message": "Database disconnected successfully",
            "previous_connection": connection_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
