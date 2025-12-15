import os
import json
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from config import SYSTEM_PROMPT
from services import AIServiceFactory, DBExecutorFactory, QueryValidator
from schemas import QuestionRequest, SQLResponse, ExecuteRequest, ExecuteResponse, DBInfoResponse, ConnectRequest, PermissionsRequest

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

# Global permission settings (can be changed per session)
allow_write_operations = False
allow_ddl_operations = False


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
            "POST /disconnect-db": "Disconnect from database",
            "POST /set-permissions": "Set query execution permissions",
            "GET /get-permissions": "Get current permissions"
        }
    }

@app.post("/generate-sql", response_model=SQLResponse)
def generate_sql(request: QuestionRequest):
    """
    Generate SQL query from natural language question.
    
    - **question**: Natural language question
    - **db_type**: Optional database type ("postgresql" or "mysql") for database-specific SQL
    - **db_schema**: Optional database schema context
    """
    try:
        # Build the user input with context
        user_input = request.question
        
        # Add database type context if provided
        if request.db_type:
            db_type_context = f"Target Database: {request.db_type.upper()}\n"
            user_input = db_type_context + user_input
        
        # Add schema context if provided
        if request.db_schema:
            user_input = f"Database Schema:\n{request.db_schema}\n\n{user_input}"
        
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
    Execute a SQL query against the connected database.
    
    Note: You must connect to a database using /connect-db before executing queries.
    
    - **query**: SQL query to execute
    - **dry_run**: If true, validates query without executing 
    """
    global db_executor, allow_write_operations, allow_ddl_operations
    
    try:
        # Check if database is connected
        if not db_executor or not db_executor.connection:
            raise HTTPException(
                status_code=400,
                detail="No database connection. Please connect to a database using /connect-db endpoint first."
            )
        
        # Get configuration
        max_rows = int(os.getenv("MAX_ROWS_RETURNED", 1000))
        
        # Validate query using global permissions
        is_valid, error_msg = QueryValidator.validate_query(
            request.query,
            allow_write=allow_write_operations,
            allow_ddl=allow_ddl_operations
        )
        
        if not is_valid:
            raise HTTPException(status_code=403, detail=error_msg)
        
        # Add LIMIT if needed for SELECT queries
        query = QueryValidator.add_limit_if_needed(request.query, max_rows)
        
        # Execute query using the persistent connection
        result = db_executor.execute_query(query, dry_run=request.dry_run)
        
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
    
    Note: Returns info only if connected via /connect-db endpoint.
    """
    global db_executor
    
    try:
        # Check if database is connected
        if not db_executor:
            raise HTTPException(
                status_code=400,
                detail="No database connection. Please connect to a database using /connect-db endpoint first."
            )
        
        info = db_executor.get_connection_info()
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

@app.post("/set-permissions")
def set_permissions(request: PermissionsRequest):
    """
    Set permissions for query execution.
    
    - **allow_write_operations**: Allow INSERT, UPDATE, DELETE operations
    - **allow_ddl_operations**: Allow CREATE, DROP, ALTER, TRUNCATE operations
    """
    global allow_write_operations, allow_ddl_operations
    
    try:
        # Update global permissions
        allow_write_operations = request.allow_write_operations
        allow_ddl_operations = request.allow_ddl_operations
        
        return {
            "success": True,
            "message": "Permissions updated successfully",
            "permissions": {
                "allow_write_operations": allow_write_operations,
                "allow_ddl_operations": allow_ddl_operations
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-permissions")
def get_permissions():
    """
    Get current query execution permissions.
    """
    global allow_write_operations, allow_ddl_operations
    
    return {
        "allow_write_operations": allow_write_operations,
        "allow_ddl_operations": allow_ddl_operations
    }

