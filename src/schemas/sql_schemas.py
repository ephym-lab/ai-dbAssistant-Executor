from pydantic import BaseModel

class QuestionRequest(BaseModel):
    """Request model for SQL generation endpoint."""
    question: str
    db_schema: str | None = None

class SQLResponse(BaseModel):
    """Response model containing SQL query and explanation."""
    content: str
    query: str
