import os
import uuid
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient, models
from qdrant_client.models import (
    Filter, FieldCondition, MatchValue, 
    Distance, VectorParams
)
from fastembed import TextEmbedding


class QdrantService:
    """Service for retrieving database schema context from Qdrant."""
    
    def __init__(self):
        """Initialize Qdrant client with configuration from environment."""
        self.url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.api_key = os.getenv("QDRANT_API_KEY")
        self.collection_name = os.getenv("QDRANT_COLLECTION_NAME", "database_schemas")
        
        # Initialize client
        if self.api_key:
            self.client = QdrantClient(url=self.url, api_key=self.api_key)
        else:
            self.client = QdrantClient(url=self.url)
    
    def health_check(self) -> Dict[str, Any]:
        """Check if Qdrant service is accessible."""
        try:
            collections = self.client.get_collections()
            return {
                "status": "healthy",
                "url": self.url,
                "collections": [col.name for col in collections.collections]
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def ensure_collection_exists(self) -> bool:
        """
        Ensure the collection exists, create if it doesn't.
        
        Creates collection configured for 384-dimensional vectors from
        FastEmbed's BAAI/bge-small-en-v1.5 model.
        
        Returns:
            True if collection exists or was created successfully
        """
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                # Create collection with vector config for FastEmbed (384 dimensions)
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=384,  # BAAI/bge-small-en-v1.5 embedding size
                        distance=Distance.COSINE
                    )
                )
                print(f"Created collection: {self.collection_name}")
            
            return True
        except Exception as e:
            print(f"Error ensuring collection exists: {e}")
            return False
    
    def ingest_schema(
        self,
        project_id: str,
        tables: List[Dict[str, Any]],
        db_type: str = "postgresql",
        clear_existing: bool = False
    ) -> Dict[str, Any]:
        """
        Ingest database schema into Qdrant.
        
        Args:
            project_id: The project identifier
            tables: List of table schemas from database
            db_type: Database type (postgresql or mysql)
            clear_existing: If True, delete existing schema for this project first
            
        Returns:
            Result dictionary with success status and details
        """
        try:
            # Ensure collection exists
            self.ensure_collection_exists()
            
            # Clear existing schema if requested
            if clear_existing:
                self.delete_project_schema(project_id)
            
            # Initialize FastEmbed for local embedding generation
            embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
            
            # Prepare documents and metadata
            documents = []
            metadata_list = []
            ids = []
            
            for table in tables:
                table_name = table.get("name", "")
                columns = table.get("columns", [])
                
                # Build text content for embedding
                content_parts = [f"Table: {table_name}"]
                
                # Add column information
                if columns:
                    content_parts.append("Columns:")
                    for col in columns:
                        if isinstance(col, dict):
                            col_name = col.get("name", "")
                            col_type = col.get("type", "")
                            nullable = col.get("nullable", True)
                            null_str = "NULL" if nullable else "NOT NULL"
                            content_parts.append(f"  - {col_name} ({col_type}) {null_str}")
                        else:
                            content_parts.append(f"  - {col}")
                
                content = "\n".join(content_parts)
                
                # Store for embedding
                documents.append(content)
                metadata_list.append({
                    "project_id": project_id,
                    "table_name": table_name,
                    "columns": columns,
                    "relationships": table.get("relationships", []),
                    "description": table.get("description", ""),
                    "db_type": db_type
                })
                ids.append(str(uuid.uuid4()))
            
            # Generate embeddings for all documents
            embeddings = list(embedding_model.embed(documents))
            
            # Create points with embeddings
            points = []
            for i, (doc_id, metadata, embedding) in enumerate(zip(ids, metadata_list, embeddings)):
                point = models.PointStruct(
                    id=doc_id,
                    payload=metadata,
                    vector=embedding.tolist()  # Convert numpy array to list
                )
                points.append(point)
            
            # Upload to Qdrant using upsert
            if points:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
            
            return {
                "success": True,
                "project_id": project_id,
                "tables_ingested": len(tables),
                "message": f"Successfully ingested {len(tables)} tables for project {project_id}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "project_id": project_id,
                "error": str(e),
                "message": f"Failed to ingest schema: {str(e)}"
            }
    
    def delete_project_schema(self, project_id: str) -> Dict[str, Any]:
        """
        Delete all schema data for a project.
        
        Args:
            project_id: The project identifier
            
        Returns:
            Result dictionary with success status
        """
        try:
            # Delete all points with this project_id
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="project_id",
                            match=MatchValue(value=project_id)
                        )
                    ]
                )
            )
            
            return {
                "success": True,
                "project_id": project_id,
                "message": f"Successfully deleted schema for project {project_id}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "project_id": project_id,
                "error": str(e),
                "message": f"Failed to delete schema: {str(e)}"
            }
    
    def retrieve_schema_context(
        self, 
        project_id: str, 
        query: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant schema chunks for a project using semantic search.
        
        Args:
            project_id: The project identifier to filter schema data
            query: User's natural language query for semantic search
            limit: Maximum number of schema chunks to retrieve
            
        Returns:
            List of schema chunks with metadata
        """
        try:
            # Generate embedding for the query using FastEmbed
            embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
            query_embedding = list(embedding_model.embed([query]))[0]
            
            # Search with project_id filter using query_points
            search_result = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding.tolist(),
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="project_id",
                            match=MatchValue(value=project_id)
                        )
                    ]
                ),
                limit=limit
            )
            
            # Extract and format results
            schema_chunks = []
            for hit in search_result.points:
                schema_chunks.append({
                    "score": hit.score,
                    "content": hit.payload.get("content", ""),
                    "metadata": {
                        "table_name": hit.payload.get("table_name"),
                        "columns": hit.payload.get("columns", []),
                        "relationships": hit.payload.get("relationships", []),
                        "description": hit.payload.get("description", "")
                    }
                })
            
            return schema_chunks
            
        except Exception as e:
            print(f"Error retrieving schema context: {e}")
            return []
    
    def get_full_schema(self, project_id: str) -> Dict[str, Any]:
        """
        Get the complete schema for a project.
        
        Args:
            project_id: The project identifier
            
        Returns:
            Complete schema information for the project
        """
        try:
            # Scroll through all points for this project
            points, _ = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="project_id",
                            match=MatchValue(value=project_id)
                        )
                    ]
                ),
                limit=100
            )
            
            # Organize schema by tables
            tables = {}
            for point in points:
                table_name = point.payload.get("table_name")
                if table_name:
                    tables[table_name] = {
                        "columns": point.payload.get("columns", []),
                        "relationships": point.payload.get("relationships", []),
                        "description": point.payload.get("description", "")
                    }
            
            return {
                "project_id": project_id,
                "tables": tables,
                "table_count": len(tables)
            }
            
        except Exception as e:
            print(f"Error retrieving full schema: {e}")
            return {
                "project_id": project_id,
                "tables": {},
                "table_count": 0,
                "error": str(e)
            }
    
    def validate_project_exists(self, project_id: str) -> bool:
        """
        Check if a project has schema data in Qdrant.
        
        Args:
            project_id: The project identifier
            
        Returns:
            True if project exists, False otherwise
        """
        try:
            points, _ = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="project_id",
                            match=MatchValue(value=project_id)
                        )
                    ]
                ),
                limit=1
            )
            
            return len(points) > 0
            
        except Exception as e:
            print(f"Error validating project: {e}")
            return False

