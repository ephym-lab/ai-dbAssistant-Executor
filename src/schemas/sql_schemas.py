from pydantic import BaseModel
from typing import List, Optional, Any

class QuestionRequest(BaseModel):
    """Request model for SQL generation endpoint."""
    question: str
    db_type: str | None = None  # "postgresql" or "mysql"
    db_schema: str | None = None
    project_id: str | None = None  # Project ID for schema context retrieval from Qdrant

class SQLResponse(BaseModel):
    """Response model containing SQL query and explanation."""
    decision: str  # "EXECUTE", "INVALID", or "EXPLAIN"
    content: str
    query: Optional[str] = None
    suggestions: Optional[List[str]] = None

class ExecuteRequest(BaseModel):
    """Request model for SQL execution endpoint."""
    query: str
    dry_run: bool = False

class ExecuteResponse(BaseModel):
    """Response model for SQL execution."""
    success: bool
    query_type: Optional[str] = None
    columns: Optional[List[str]] = None
    rows: Optional[List[List[Any]]] = None
    row_count: Optional[int] = None
    affected_rows: Optional[int] = None
    message: Optional[str] = None
    error: Optional[str] = None
    dry_run: bool = False
    explain: Optional[Any] = None

class ColumnInfo(BaseModel):
    """Column information model."""
    name: str
    type: str
    nullable: bool

class TableInfo(BaseModel):
    """Table information model."""
    name: str
    columns: List[ColumnInfo]

class DBInfoResponse(BaseModel):
    """Response model for database connection info."""
    type: str
    host: str
    port: int
    database: str
    database_name: str  # Alias for database
    connected: bool
    tables: List[TableInfo] = []

class ConnectRequest(BaseModel):
    """Request model for database connection endpoint."""
    db_type: str  # "postgresql" or "mysql"
    connection_string: str
    project_id: Optional[int] = None  # Project ID to fetch permissions from Go backend

class SchemaRequest(BaseModel):
    """Request model for schema retrieval endpoint."""
    db_type: str  # "postgresql" or "mysql"
    connection_string: str

class SchemaResponse(BaseModel):
    """Response model for schema information."""
    db_type: str
    database: str
    host: str
    port: int
    table_count: int
    tables: List[TableInfo]

class IngestSchemaRequest(BaseModel):
    """Request model for schema ingestion endpoint."""
    project_id: str
    db_type: str  # "postgresql" or "mysql"
    connection_string: str
    clear_existing: bool = False  # If True, clear existing schema before ingesting

class IngestSchemaResponse(BaseModel):
    """Response model for schema ingestion."""
    success: bool
    project_id: str
    tables_ingested: Optional[int] = None
    message: str
    error: Optional[str] = None

class UpdateSchemaRequest(BaseModel):
    """Request model for schema update endpoint."""
    project_id: str
    db_type: str  # "postgresql" or "mysql"
    connection_string: str

class QdrantSchemaRequest(BaseModel):
    """Request model for retrieving schema from Qdrant."""
    project_id: str

class QdrantSchemaResponse(BaseModel):
    """Response model for schema retrieved from Qdrant."""
    success: bool
    project_id: str
    db_type: Optional[str] = None
    table_count: int
    tables: List[TableInfo]
    message: Optional[str] = None
    error: Optional[str] = None






