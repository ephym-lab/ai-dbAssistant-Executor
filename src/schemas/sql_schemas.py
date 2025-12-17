from pydantic import BaseModel
from typing import List, Optional, Any

class QuestionRequest(BaseModel):
    """Request model for SQL generation endpoint."""
    question: str
    db_type: str | None = None  # "postgresql" or "mysql"
    db_schema: str | None = None

class SQLResponse(BaseModel):
    """Response model containing SQL query and explanation."""
    content: str
    query: str

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





