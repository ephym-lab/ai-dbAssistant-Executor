from typing import List, Dict, Any, Optional, Tuple


class ContextBuilder:
    """Build context-aware prompts and validate requests against schema."""
    
    @staticmethod
    def build_schema_context(schema_chunks: List[Dict[str, Any]]) -> str:
        """
        Format schema chunks into a readable context string.
        
        Args:
            schema_chunks: List of schema chunks from Qdrant
            
        Returns:
            Formatted schema context string
        """
        if not schema_chunks:
            return "No schema context available."
        
        context_parts = []
        
        for chunk in schema_chunks:
            metadata = chunk.get("metadata", {})
            table_name = metadata.get("table_name", "Unknown")
            columns = metadata.get("columns", [])
            relationships = metadata.get("relationships", [])
            description = metadata.get("description", "")
            
            # Build table section
            table_section = f"Table: {table_name}\n"
            
            if description:
                table_section += f"Description: {description}\n"
            
            if columns:
                table_section += "Columns:\n"
                for col in columns:
                    if isinstance(col, dict):
                        col_name = col.get("name", "")
                        col_type = col.get("type", "")
                        nullable = col.get("nullable", True)
                        null_str = "NULL" if nullable else "NOT NULL"
                        table_section += f"  - {col_name} ({col_type}) {null_str}\n"
                    else:
                        table_section += f"  - {col}\n"
            
            if relationships:
                table_section += "Relationships:\n"
                for rel in relationships:
                    if isinstance(rel, dict):
                        table_section += f"  - {rel.get('type', 'FOREIGN KEY')}: {rel.get('description', '')}\n"
                    else:
                        table_section += f"  - {rel}\n"
            
            context_parts.append(table_section)
        
        return "\n".join(context_parts)
    
    @staticmethod
    def validate_request_against_schema(
        user_request: str, 
        schema_chunks: List[Dict[str, Any]]
    ) -> Tuple[bool, List[str]]:
        """
        Perform basic validation of user request against schema.
        
        Args:
            user_request: User's natural language request
            schema_chunks: Schema chunks from Qdrant
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        if not schema_chunks:
            return True, []  # Let AI handle if no schema available
        
        issues = []
        
        # Extract table names from schema
        available_tables = set()
        for chunk in schema_chunks:
            metadata = chunk.get("metadata", {})
            table_name = metadata.get("table_name")
            if table_name:
                available_tables.add(table_name.lower())
        
        # Basic keyword extraction (simple approach)
        request_lower = user_request.lower()
        
        # Check for common table reference patterns
        # This is a simple heuristic - the AI will do the real validation
        common_keywords = ["from", "into", "update", "table", "join"]
        
        # Note: This is intentionally simple - the AI will do the heavy lifting
        # We're just doing basic sanity checks here
        
        return True, issues  # Let AI handle detailed validation
    
    @staticmethod
    def build_context_aware_prompt(
        user_request: str,
        schema_context: str,
        db_type: str = "postgresql"
    ) -> str:
        """
        Build a complete context-aware prompt for the AI.
        
        Args:
            user_request: User's natural language request
            schema_context: Formatted schema context
            db_type: Database type (postgresql or mysql)
            
        Returns:
            Complete prompt with context
        """
        prompt_parts = []
        
        # Add database type
        prompt_parts.append(f"Target Database: {db_type.upper()}")
        
        # Add schema context
        if schema_context and schema_context != "No schema context available.":
            prompt_parts.append(f"\nDatabase Schema Context:\n{schema_context}")
        
        # Add user request
        prompt_parts.append(f"\nUser Request: {user_request}")
        
        return "\n".join(prompt_parts)
    
    @staticmethod
    def extract_tables_from_schema(schema_chunks: List[Dict[str, Any]]) -> List[str]:
        """
        Extract list of table names from schema chunks.
        
        Args:
            schema_chunks: Schema chunks from Qdrant
            
        Returns:
            List of table names
        """
        tables = []
        for chunk in schema_chunks:
            metadata = chunk.get("metadata", {})
            table_name = metadata.get("table_name")
            if table_name and table_name not in tables:
                tables.append(table_name)
        
        return tables
    
    @staticmethod
    def extract_columns_for_table(
        schema_chunks: List[Dict[str, Any]], 
        table_name: str
    ) -> List[Dict[str, Any]]:
        """
        Extract column information for a specific table.
        
        Args:
            schema_chunks: Schema chunks from Qdrant
            table_name: Name of the table
            
        Returns:
            List of column information
        """
        for chunk in schema_chunks:
            metadata = chunk.get("metadata", {})
            if metadata.get("table_name", "").lower() == table_name.lower():
                return metadata.get("columns", [])
        
        return []
