import os
import re
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

class QueryType(Enum):
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    DDL = "DDL"  # CREATE, DROP, ALTER, TRUNCATE
    UNKNOWN = "UNKNOWN"

class QueryValidator:
    """Validates and classifies SQL queries for safety."""
    
    DDL_KEYWORDS = ['CREATE', 'DROP', 'ALTER', 'TRUNCATE', 'RENAME']
    WRITE_KEYWORDS = ['INSERT', 'UPDATE', 'DELETE']
    
    @staticmethod
    def detect_query_type(query: str) -> QueryType:
        """Detect the type of SQL query."""
        query_upper = query.strip().upper()
        
        # Check for DDL
        for keyword in QueryValidator.DDL_KEYWORDS:
            if query_upper.startswith(keyword):
                return QueryType.DDL
        
        # Check for write operations
        if query_upper.startswith('INSERT'):
            return QueryType.INSERT
        elif query_upper.startswith('UPDATE'):
            return QueryType.UPDATE
        elif query_upper.startswith('DELETE'):
            return QueryType.DELETE
        elif query_upper.startswith('SELECT'):
            return QueryType.SELECT
        
        return QueryType.UNKNOWN
    
    @staticmethod
    def validate_query(query: str, allow_write: bool = False, allow_ddl: bool = False) -> Tuple[bool, str]:
        """
        Validate if a query is safe to execute based on configuration.
        Returns (is_valid, error_message)
        """
        if not query or not query.strip():
            return False, "Query cannot be empty"
        
        query_type = QueryValidator.detect_query_type(query)
        
        if query_type == QueryType.UNKNOWN:
            return False, "Unknown or unsupported query type"
        
        if query_type == QueryType.DDL and not allow_ddl:
            return False, f"DDL operations are disabled. Query type: {query_type.value}"
        
        if query_type in [QueryType.INSERT, QueryType.UPDATE, QueryType.DELETE] and not allow_write:
            return False, f"Write operations are disabled. Query type: {query_type.value}"
        
        return True, ""
    
    @staticmethod
    def add_limit_if_needed(query: str, max_rows: int) -> str:
        """Add LIMIT clause to SELECT queries if not present."""
        query_upper = query.strip().upper()
        
        if not query_upper.startswith('SELECT'):
            return query
        
        # Check if LIMIT already exists
        if 'LIMIT' in query_upper:
            return query
        
        # Add LIMIT
        return f"{query.rstrip(';')} LIMIT {max_rows};"


class DBExecutor(ABC):
    """Abstract base class for database executors."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = None
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish database connection."""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Close database connection."""
        pass
    
    @abstractmethod
    def execute_query(self, query: str, dry_run: bool = False) -> Dict[str, Any]:
        """Execute a SQL query and return results."""
        pass
    
    @abstractmethod
    def get_connection_info(self) -> Dict[str, Any]:
        """Get database connection information."""
        pass


class PostgreSQLExecutor(DBExecutor):
    """PostgreSQL database executor."""
    
    def connect(self) -> bool:
        try:
            import psycopg2
            self.connection = psycopg2.connect(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 5432),
                database=self.config.get('database'),
                user=self.config.get('user'),
                password=self.config.get('password')
            )
            return True
        except Exception as e:
            raise Exception(f"PostgreSQL connection failed: {str(e)}")
    
    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def execute_query(self, query: str, dry_run: bool = False) -> Dict[str, Any]:
        """Execute query and return results."""
        if not self.connection:
            self.connect()
        
        cursor = self.connection.cursor()
        
        try:
            if dry_run:
                # Use EXPLAIN for dry run
                explain_query = f"EXPLAIN {query}"
                cursor.execute(explain_query)
                explain_result = cursor.fetchall()
                return {
                    "success": True,
                    "dry_run": True,
                    "explain": [row[0] for row in explain_result],
                    "message": "Dry run completed (query not executed)"
                }
            
            # Execute the actual query
            cursor.execute(query)
            
            query_type = QueryValidator.detect_query_type(query)
            
            if query_type == QueryType.SELECT:
                # Fetch results for SELECT
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                
                return {
                    "success": True,
                    "query_type": query_type.value,
                    "columns": columns,
                    "rows": [list(row) for row in rows],
                    "row_count": len(rows)
                }
            else:
                # For write operations, commit and return affected rows
                self.connection.commit()
                return {
                    "success": True,
                    "query_type": query_type.value,
                    "affected_rows": cursor.rowcount,
                    "message": f"{query_type.value} operation completed successfully"
                }
        
        except Exception as e:
            self.connection.rollback()
            return {
                "success": False,
                "error": str(e),
                "message": "Query execution failed"
            }
        finally:
            cursor.close()
    
    def get_connection_info(self) -> Dict[str, Any]:
        return {
            "type": "PostgreSQL",
            "host": self.config.get('host'),
            "port": self.config.get('port'),
            "database": self.config.get('database'),
            "connected": self.connection is not None
        }


class MySQLExecutor(DBExecutor):
    """MySQL database executor."""
    
    def connect(self) -> bool:
        try:
            import mysql.connector
            self.connection = mysql.connector.connect(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 3306),
                database=self.config.get('database'),
                user=self.config.get('user'),
                password=self.config.get('password')
            )
            return True
        except Exception as e:
            raise Exception(f"MySQL connection failed: {str(e)}")
    
    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def execute_query(self, query: str, dry_run: bool = False) -> Dict[str, Any]:
        """Execute query and return results."""
        if not self.connection:
            self.connect()
        
        cursor = self.connection.cursor()
        
        try:
            if dry_run:
                # Use EXPLAIN for dry run
                explain_query = f"EXPLAIN {query}"
                cursor.execute(explain_query)
                explain_result = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                return {
                    "success": True,
                    "dry_run": True,
                    "explain": {
                        "columns": columns,
                        "rows": [list(row) for row in explain_result]
                    },
                    "message": "Dry run completed (query not executed)"
                }
            
            # Execute the actual query
            cursor.execute(query)
            
            query_type = QueryValidator.detect_query_type(query)
            
            if query_type == QueryType.SELECT:
                # Fetch results for SELECT
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                
                return {
                    "success": True,
                    "query_type": query_type.value,
                    "columns": columns,
                    "rows": [list(row) for row in rows],
                    "row_count": len(rows)
                }
            else:
                # For write operations, commit and return affected rows
                self.connection.commit()
                return {
                    "success": True,
                    "query_type": query_type.value,
                    "affected_rows": cursor.rowcount,
                    "message": f"{query_type.value} operation completed successfully"
                }
        
        except Exception as e:
            self.connection.rollback()
            return {
                "success": False,
                "error": str(e),
                "message": "Query execution failed"
            }
        finally:
            cursor.close()
    
    def get_connection_info(self) -> Dict[str, Any]:
        return {
            "type": "MySQL",
            "host": self.config.get('host'),
            "port": self.config.get('port'),
            "database": self.config.get('database'),
            "connected": self.connection is not None
        }


class DBExecutorFactory:
    """Factory for creating database executors."""
    
    @staticmethod
    def get_executor() -> Optional[DBExecutor]:
        """Create and return appropriate database executor based on environment."""
        db_type = os.getenv("DB_TYPE", "").lower()
        
        if db_type == "postgresql":
            config = {
                'host': os.getenv("POSTGRES_HOST", "localhost"),
                'port': int(os.getenv("POSTGRES_PORT", 5432)),
                'database': os.getenv("POSTGRES_DB"),
                'user': os.getenv("POSTGRES_USER"),
                'password': os.getenv("POSTGRES_PASSWORD")
            }
            return PostgreSQLExecutor(config)
        
        elif db_type == "mysql":
            config = {
                'host': os.getenv("MYSQL_HOST", "localhost"),
                'port': int(os.getenv("MYSQL_PORT", 3306)),
                'database': os.getenv("MYSQL_DB"),
                'user': os.getenv("MYSQL_USER"),
                'password': os.getenv("MYSQL_PASSWORD")
            }
            return MySQLExecutor(config)
        
        return None
    
    @staticmethod
    def from_connection_string(db_type: str, connection_string: str) -> Optional[DBExecutor]:
        """
        Create and return appropriate database executor from connection string.
        
        Args:
            db_type: Database type ("postgresql" or "mysql")
            connection_string: Connection string in format:
                - PostgreSQL: postgresql://user:password@host:port/database
                - MySQL: mysql://user:password@host:port/database
        """
        try:
            from urllib.parse import urlparse
            
            # Normalize db_type
            db_type = db_type.lower().strip()
            
            # Validate db_type
            if db_type not in ['postgresql', 'postgres', 'mysql']:
                raise ValueError(f"Unsupported database type: {db_type}. Supported types: postgresql, mysql")
            
            # Parse the connection string
            parsed = urlparse(connection_string)
            
            # Extract components
            user = parsed.username
            password = parsed.password
            host = parsed.hostname or 'localhost'
            port = parsed.port
            database = parsed.path.lstrip('/') if parsed.path else None
            
            # Validate required fields
            if not user:
                raise ValueError("Username is required in connection string")
            if not database:
                raise ValueError("Database name is required in connection string")
            
            # Create executor based on db_type
            if db_type in ['postgresql', 'postgres']:
                config = {
                    'host': host,
                    'port': port or 5432,
                    'database': database,
                    'user': user,
                    'password': password
                }
                return PostgreSQLExecutor(config)
            
            elif db_type == 'mysql':
                config = {
                    'host': host,
                    'port': port or 3306,
                    'database': database,
                    'user': user,
                    'password': password
                }
                return MySQLExecutor(config)
        
        except Exception as e:
            raise ValueError(f"Invalid connection string: {str(e)}")

