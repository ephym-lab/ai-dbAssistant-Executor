import os
import json
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from src.config.prompts import SYSTEM_PROMPT
from src.services import AIServiceFactory, DBExecutorFactory, QueryValidator
from src.schemas import (
    QuestionRequest, SQLResponse, ExecuteRequest, ExecuteResponse, 
    DBInfoResponse, ConnectRequest, SchemaRequest, SchemaResponse,
    IngestSchemaRequest, IngestSchemaResponse, UpdateSchemaRequest
)

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
        "message": "AI SQL Assistant API - Context-Aware Edition",
        "service": ai_service.__class__.__name__,
        "features": [
            "Context-aware SQL generation with Qdrant schema retrieval",
            "Request validation against actual database schema",
            "Intelligent suggestions for invalid requests",
            "Automatic schema ingestion from database to Qdrant"
        ],
        "endpoints": {
            "POST /generate-sql": "Generate SQL from natural language (supports project_id for schema context)",
            "POST /execute-sql": "Execute SQL query",
            "POST /validate-sql": "Validate SQL query (dry-run)",
            "GET /db-info": "Database connection information",
            "POST /connect-db": "Connect to database (requires project_id)",
            "POST /disconnect-db": "Disconnect from database",
            "POST /get-schema": "Get database schema and table information",
            "POST /ingest-schema": "Ingest database schema into Qdrant for context-aware generation",
            "POST /update-schema": "Update existing project schema in Qdrant (replaces old schema)"
        }
    }

@app.post("/generate-sql", response_model=SQLResponse)
def generate_sql(request: QuestionRequest):
    """
    Generate SQL query from natural language question with context-awareness.
    
    - **question**: Natural language question
    - **db_type**: Optional database type ("postgresql" or "mysql") for database-specific SQL
    - **db_schema**: Optional database schema context (legacy support)
    - **project_id**: Optional project ID for retrieving schema from Qdrant
    """
    try:
        from src.services import QdrantService, ContextBuilder
        
        # Build the user input with context
        user_input = request.question
        schema_context = ""
        
        # Try to retrieve schema from Qdrant if project_id is provided
        if request.project_id:
            try:
                qdrant_service = QdrantService()
                
                # Retrieve relevant schema chunks using semantic search
                schema_chunks = qdrant_service.retrieve_schema_context(
                    project_id=request.project_id,
                    query=request.question,
                    limit=5
                )
                
                # Build formatted schema context
                if schema_chunks:
                    schema_context = ContextBuilder.build_schema_context(schema_chunks)
                else:
                    # No schema found for this project
                    schema_context = f"No schema context found for project_id: {request.project_id}"
                    
            except Exception as e:
                print(f"Error retrieving schema from Qdrant: {e}")
                schema_context = f"Error retrieving schema: {str(e)}"
        
        # Fallback to legacy db_schema if provided and no Qdrant context
        elif request.db_schema:
            schema_context = request.db_schema
        
        # Build context-aware prompt
        if schema_context and schema_context != "No schema context available.":
            user_input = ContextBuilder.build_context_aware_prompt(
                user_request=request.question,
                schema_context=schema_context,
                db_type=request.db_type or "postgresql"
            )
        elif request.db_type:
            # Add database type context if provided but no schema
            db_type_context = f"Target Database: {request.db_type.upper()}\n"
            user_input = db_type_context + user_input
        
        # Get response from AI service
        response_str = ai_service.get_response(user_input, SYSTEM_PROMPT)
        
        # Clean and parse JSON response
        clean_str = response_str
        if "```" in clean_str:
            clean_str = clean_str.replace("```json", "").replace("```", "").strip()
        
        try:
            response_json = json.loads(clean_str)
            
            # Ensure all required fields are present
            decision = response_json.get("decision", "EXECUTE")
            content = response_json.get("content", "")
            query = response_json.get("query")
            suggestions = response_json.get("suggestions", [])
            
            # Handle legacy responses that don't have decision field
            if "decision" not in response_json:
                # If there's a query, assume EXECUTE
                if query:
                    decision = "EXECUTE"
                else:
                    decision = "EXPLAIN"
            
            return SQLResponse(
                decision=decision,
                content=content,
                query=query,
                suggestions=suggestions if suggestions else []
            )
        except json.JSONDecodeError:
            # If response is not valid JSON, return it as an error
            return SQLResponse(
                decision="EXPLAIN",
                content=f"Error parsing AI response: {response_str}",
                query=None,
                suggestions=[]
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
    Validation is handled by the Go backend.
    
    - **query**: SQL query to execute
    - **dry_run**: If true, validates query without executing 
    """
    global db_executor
    
    try:
        # Check if database is connected
        if not db_executor or not db_executor.connection:
            raise HTTPException(
                status_code=400,
                detail="No database connection. Please connect to a database using /connect-db endpoint first."
            )
        
        # Get configuration
        max_rows = int(os.getenv("MAX_ROWS_RETURNED", 1000))
        
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
    Get database connection information and table schema.
    
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
        tables = db_executor.get_table_schema()
        
        # Add database_name alias and tables
        info["database_name"] = info["database"]
        info["tables"] = tables
        
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
    - **project_id**: Project ID (stored for reference, validation handled by Go backend)
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
            "connection_info": db_executor.get_connection_info(),
            "project_id": request.project_id
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

@app.post("/get-schema", response_model=SchemaResponse)
def get_schema(request: SchemaRequest):
    """
    Get database schema and table information.
    
    Creates a temporary connection to fetch schema information.
    
    - **db_type**: Database type ("postgresql" or "mysql")
    - **connection_string**: Database connection string
    """
    temp_executor = None
    
    try:
        # Create temporary executor from connection string
        temp_executor = DBExecutorFactory.from_connection_string(
            db_type=request.db_type,
            connection_string=request.connection_string
        )
        if not temp_executor:
            raise HTTPException(
                status_code=400,
                detail="Failed to create database executor from connection string."
            )
        
        # Connect to database
        temp_executor.connect()
        
        # Get table schema
        tables = temp_executor.get_table_schema()
        
        # Get connection info
        conn_info = temp_executor.get_connection_info()
        
        # Disconnect from database
        temp_executor.disconnect()
        
        return SchemaResponse(
            db_type=conn_info["type"],
            database=conn_info["database"],
            host=conn_info["host"],
            port=conn_info["port"],
            table_count=len(tables),
            tables=tables
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Ensure connection is closed even if an error occurs
        if temp_executor and temp_executor.connection:
            try:
                temp_executor.disconnect()
            except:
                pass

@app.post("/ingest-schema", response_model=IngestSchemaResponse)
def ingest_schema(request: IngestSchemaRequest):
    """
    Ingest database schema into Qdrant for context-aware SQL generation.
    
    This endpoint:
    1. Connects to the specified database
    2. Retrieves the complete schema (tables, columns, types)
    3. Stores it in Qdrant with the project_id for later retrieval
    
    - **project_id**: Project identifier for schema isolation
    - **db_type**: Database type ("postgresql" or "mysql")
    - **connection_string**: Database connection string
    - **clear_existing**: If True, delete existing schema for this project first
    """
    temp_executor = None
    
    try:
        from src.services import QdrantService
        
        # Create temporary executor from connection string
        temp_executor = DBExecutorFactory.from_connection_string(
            db_type=request.db_type,
            connection_string=request.connection_string
        )
        if not temp_executor:
            raise HTTPException(
                status_code=400,
                detail="Failed to create database executor from connection string."
            )
        
        # Connect to database
        temp_executor.connect()
        
        # Get table schema
        tables = temp_executor.get_table_schema()
        
        if not tables:
            return IngestSchemaResponse(
                success=False,
                project_id=request.project_id,
                tables_ingested=0,
                message="No tables found in database",
                error="Database has no tables or schema retrieval failed"
            )
        
        # Disconnect from database
        temp_executor.disconnect()
        
        # Ingest schema into Qdrant
        qdrant_service = QdrantService()
        result = qdrant_service.ingest_schema(
            project_id=request.project_id,
            tables=tables,
            db_type=request.db_type,
            clear_existing=request.clear_existing
        )
        
        return IngestSchemaResponse(
            success=result["success"],
            project_id=result["project_id"],
            tables_ingested=result.get("tables_ingested"),
            message=result["message"],
            error=result.get("error")
        )
        
    except ValueError as e:
        return IngestSchemaResponse(
            success=False,
            project_id=request.project_id,
            message=f"Validation error: {str(e)}",
            error=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        return IngestSchemaResponse(
            success=False,
            project_id=request.project_id,
            message=f"Failed to ingest schema: {str(e)}",
            error=str(e)
        )
    finally:
        # Ensure connection is closed even if an error occurs
        if temp_executor and temp_executor.connection:
            try:
                temp_executor.disconnect()
            except:
                pass


@app.post("/update-schema", response_model=IngestSchemaResponse)
def update_schema(request: UpdateSchemaRequest):
    """
    Update existing project schema in Qdrant.
    
    This endpoint:
    1. Deletes the existing schema for the project
    2. Connects to the database
    3. Retrieves the fresh schema
    4. Stores the updated schema in Qdrant
    
    This is a convenience endpoint that automatically sets clear_existing=True.
    Use this when your database schema has changed and you want to refresh it.
    
    - **project_id**: Project identifier
    - **db_type**: Database type ("postgresql" or "mysql")
    - **connection_string**: Database connection string
    """
    temp_executor = None
    
    try:
        from src.services import QdrantService
        
        # Create temporary executor from connection string
        temp_executor = DBExecutorFactory.from_connection_string(
            db_type=request.db_type,
            connection_string=request.connection_string
        )
        if not temp_executor:
            raise HTTPException(
                status_code=400,
                detail="Failed to create database executor from connection string."
            )
        
        # Connect to database
        temp_executor.connect()
        
        # Get table schema
        tables = temp_executor.get_table_schema()
        
        if not tables:
            return IngestSchemaResponse(
                success=False,
                project_id=request.project_id,
                tables_ingested=0,
                message="No tables found in database",
                error="Database has no tables or schema retrieval failed"
            )
        
        # Disconnect from database
        temp_executor.disconnect()
        
        # Update schema in Qdrant (clear_existing=True)
        qdrant_service = QdrantService()
        result = qdrant_service.ingest_schema(
            project_id=request.project_id,
            tables=tables,
            db_type=request.db_type,
            clear_existing=True  # Always clear when updating
        )
        
        return IngestSchemaResponse(
            success=result["success"],
            project_id=result["project_id"],
            tables_ingested=result.get("tables_ingested"),
            message=f"Updated schema: {result['message']}",
            error=result.get("error")
        )
        
    except ValueError as e:
        return IngestSchemaResponse(
            success=False,
            project_id=request.project_id,
            message=f"Validation error: {str(e)}",
            error=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        return IngestSchemaResponse(
            success=False,
            project_id=request.project_id,
            message=f"Failed to update schema: {str(e)}",
            error=str(e)
        )
    finally:
        # Ensure connection is closed even if an error occurs
        if temp_executor and temp_executor.connection:
            try:
                temp_executor.disconnect()
            except:
                pass
