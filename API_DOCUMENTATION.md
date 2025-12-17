# API Endpoints Documentation

Complete documentation for all AI SQL Assistant API endpoints.

## Table of Contents
- [SQL Generation Endpoint](#sql-generation-endpoint)
- [Connection Management Endpoints](#connection-management-endpoints)
- [Query Execution Endpoints](#query-execution-endpoints)
- [Database Info Endpoint](#database-info-endpoint)
- [Permissions](#permissions)

---

## SQL Generation Endpoint

### POST /generate-sql

Generate SQL queries from natural language questions using AI.

**Request:**
```bash
curl -X POST http://localhost:8000/generate-sql \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Get all users who registered in the last 30 days",
    "db_type": "postgresql",
    "db_schema": "users table with id, username, email, created_at columns"
  }'
```

**Request Body:**
```json
{
  "question": "Get all users who registered in the last 30 days",
  "db_type": "postgresql",
  "db_schema": "users table with id, username, email, created_at columns"
}
```

**Parameters:**
- `question` (required): Natural language question describing what SQL you need
- `db_type` (optional): Database type (`"postgresql"` or `"mysql"`) for database-specific SQL syntax
- `db_schema` (optional): Database schema context to help generate accurate queries

**Response:**
```json
{
  "content": "This query selects all users where the created_at timestamp is within the last 30 days...",
  "query": "SELECT * FROM users WHERE created_at >= NOW() - INTERVAL '30 days';"
}
```

**Benefits of using `db_type`:**
- Generates database-specific SQL syntax (e.g., PostgreSQL uses `INTERVAL '30 days'`, MySQL uses `INTERVAL 30 DAY`)
- Uses appropriate functions for each database (e.g., PostgreSQL's JSONB operators vs MySQL's JSON functions)
- Ensures compatibility with the target database

**Example with Python:**
```python
import requests

response = requests.post("http://localhost:8000/generate-sql", json={
    "question": "Find users with email domain gmail.com",
    "db_type": "postgresql",
    "db_schema": "users(id, username, email, created_at)"
})

result = response.json()
print(f"SQL: {result['query']}")
```

---

## Connection Management Endpoints

### POST /connect-db

Establish a persistent connection to the database using a connection string and project ID.

> [!IMPORTANT]
> This endpoint now requires a `project_id` parameter. Permissions are fetched from the Go backend based on this project ID.

**Request:**
```bash
curl -X POST http://localhost:8000/connect-db \
  -H "Content-Type: application/json" \
  -d '{
    "db_type": "postgresql",
    "connection_string": "postgresql://user:password@localhost:5432/mydb",
    "project_id": 1
  }'
```

**Request Body:**
```json
{
  "db_type": "postgresql",
  "connection_string": "postgresql://user:password@localhost:5432/mydb",
  "project_id": 1
}
```

**Parameters:**
- `db_type` (required): Database type - either `"postgresql"` or `"mysql"`
- `connection_string` (required): Database connection string
- `project_id` (required): Project ID to fetch permissions from Go backend

**Supported Connection String Formats:**
- PostgreSQL: `postgresql://user:password@host:port/database`
- MySQL: `mysql://user:password@host:port/database`

**Response (Success):**
```json
{
  "success": true,
  "message": "Database connected successfully",
  "connection_info": {
    "type": "PostgreSQL",
    "host": "localhost",
    "port": 5432,
    "database": "mydb",
    "connected": true
  },
  "project_id": 1
}
```

### POST /disconnect-db

Close the database connection and clear project context.

**Request:**
```bash
curl -X POST http://localhost:8000/disconnect-db
```

**Response:**
```json
{
  "success": true,
  "message": "Database disconnected successfully",
  "previous_connection": {
    "type": "PostgreSQL",
    "host": "localhost",
    "port": 5432,
    "database": "mydb",
    "connected": false
  }
}
```

---

## Query Execution Endpoints

### POST /execute-sql

Execute a SQL query against the connected database.

**Request:**
```bash
curl -X POST http://localhost:8000/execute-sql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT * FROM users LIMIT 10",
    "dry_run": false
  }'
```

**Request Body:**
```json
{
  "query": "SELECT * FROM users LIMIT 10",
  "dry_run": false
}
```

**Parameters:**
- `query` (required): SQL query to execute
- `dry_run` (optional): If `true`, validates query without executing (default: `false`)

**Response (SELECT query):**
```json
{
  "success": true,
  "query_type": "SELECT",
  "columns": ["id", "username", "email"],
  "rows": [
    [1, "john_doe", "john@example.com"],
    [2, "jane_smith", "jane@example.com"]
  ],
  "row_count": 2
}
```

**Response (INSERT/UPDATE/DELETE):**
```json
{
  "success": true,
  "query_type": "INSERT",
  "affected_rows": 1,
  "message": "INSERT operation completed successfully"
}
```

### POST /validate-sql

Validate SQL query without executing (dry-run mode).

> [!NOTE]
> Permissions are still checked during validation based on the project_id from the connection.

**Request:**
```bash
curl -X POST http://localhost:8000/validate-sql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "SELECT * FROM users WHERE id = 1"
  }'
```

**Response:**
```json
{
  "success": true,
  "dry_run": true,
  "explain": ["Seq Scan on users", "Filter: (id = 1)"],
  "message": "Dry run completed (query not executed)"
}
```

---

## Database Info Endpoint

### GET /db-info

Get information about the current database connection.

**Request:**
```bash
curl http://localhost:8000/db-info
```

**Response (Connected):**
```json
{
  "type": "PostgreSQL",
  "host": "localhost",
  "port": 5432,
  "database": "mydb",
  "connected": true
}
```

**Response (Not Connected):**
```json
{
  "type": "PostgreSQL",
  "host": "localhost",
  "port": 5432,
  "database": "mydb",
  "connected": false
}
```

---

## Complete Workflow Example

Here's a complete example showing how to use all endpoints together:

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Generate SQL using AI
print("1. Generating SQL...")
gen_response = requests.post(f"{BASE_URL}/generate-sql", json={
    "question": "Get all active users",
    "db_type": "postgresql",
    "db_schema": "users(id, username, email, is_active, created_at)"
})
sql_query = gen_response.json()["query"]
print(f"Generated SQL: {sql_query}")

# 2. Connect to database with project_id
print("\n2. Connecting to database...")
connect_response = requests.post(f"{BASE_URL}/connect-db", json={
    "db_type": "postgresql",
    "connection_string": "postgresql://user:pass@localhost:5432/mydb",
    "project_id": 1  # Project ID from Go backend
})
print(f"Connected: {connect_response.json()['success']}")

# 3. Check connection info
print("\n3. Checking connection...")
info_response = requests.get(f"{BASE_URL}/db-info")
print(f"Connection info: {info_response.json()}")

# 4. Validate the generated SQL (dry-run)
print("\n4. Validating SQL...")
validate_response = requests.post(f"{BASE_URL}/validate-sql", json={
    "query": sql_query
})
print(f"Validation: {validate_response.json()['message']}")

# 5. Execute the query
print("\n5. Executing SQL...")
execute_response = requests.post(f"{BASE_URL}/execute-sql", json={
    "query": sql_query,
    "dry_run": False
})
result = execute_response.json()
print(f"Rows returned: {result.get('row_count')}")
print(f"Data: {result.get('rows')}")

# 6. Disconnect
print("\n6. Disconnecting...")
disconnect_response = requests.post(f"{BASE_URL}/disconnect-db")
print(f"Disconnected: {disconnect_response.json()['success']}")
```

---

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK`: Request successful
- `400 Bad Request`: Invalid input (e.g., invalid connection string, unsupported db_type)
- `403 Forbidden`: Operation not allowed (e.g., write operations disabled)
- `500 Internal Server Error`: Server error (e.g., database connection failed)

**Error Response Format:**
```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Configuration

### Go Backend Integration

The Python service acts as a stateless proxy for database operations:

```bash
# Go Backend URL (optional, for future features)
GO_BACKEND_URL=http://localhost:8080
```

**Permission validation is handled by the Go backend:**
- The Python service executes queries without validation
- The Go backend is responsible for validating permissions before sending queries to the Python proxy
- This keeps the Python service simple and stateless

> [!IMPORTANT]
> The Python service does not validate permissions. All permission checks should be performed in the Go backend before calling the Python API.

### Security Settings

Configure query execution permissions via environment variables:

```bash
# Maximum rows returned for SELECT queries
MAX_ROWS_RETURNED=1000
```

> [!NOTE]
> The `ALLOW_WRITE_OPERATIONS` and `ALLOW_DDL_OPERATIONS` environment variables are no longer used. Permissions are now managed by the Go backend.


### AI Service Configuration

Set your AI provider:

```bash
# Use OpenAI
AI_PROVIDER=openai
OPENAI_API_KEY=your_key_here

# Or use Gemini
AI_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
```

---

## Permissions

### Overview

The Python FastAPI service acts as a **stateless proxy** for database operations. All permission validation is handled by the Go backend before queries are sent to the Python service.

### Architecture

The Python service:
- ✅ Connects to databases
- ✅ Executes SQL queries
- ✅ Returns results
- ❌ Does NOT validate permissions
- ❌ Does NOT fetch permissions from Go backend

The Go backend:
- ✅ Manages project permissions
- ✅ Validates queries against permissions
- ✅ Sends validated queries to Python proxy
- ✅ Handles all business logic

### Permission Model

The Go backend manages four types of permissions:

| Permission | Description | Allowed Operations |
|------------|-------------|-------------------|
| `allow_read` | Allow read operations | `SELECT` |
| `allow_write` | Allow write operations | `INSERT`, `UPDATE` |
| `allow_delete` | Allow delete operations | `DELETE` |
| `allow_ddl` | Allow DDL operations | `CREATE`, `DROP`, `ALTER`, `TRUNCATE` |

### How It Works

```mermaid
sequenceDiagram
    participant Client
    participant Go Backend
    participant Python Proxy
    participant Database

    Client->>Go Backend: Execute query request
    Go Backend->>Go Backend: Validate permissions
    alt Permissions OK
        Go Backend->>Python Proxy: POST /connect-db
        Python Proxy->>Database: Connect
        Go Backend->>Python Proxy: POST /execute-sql
        Python Proxy->>Database: Execute query
        Database-->>Python Proxy: Results
        Python Proxy-->>Go Backend: Results
        Go Backend-->>Client: Results
    else Permission Denied
        Go Backend-->>Client: 403 Forbidden
    end
```

### Integration Flow

1. **Client** sends query request to **Go Backend**
2. **Go Backend** validates permissions for the project
3. If allowed, **Go Backend** calls **Python Proxy** to execute query
4. **Python Proxy** executes query and returns results
5. **Go Backend** returns results to **Client**

### Setting Up

1. **Configure project permissions** in the Go backend database

2. **Connect to database** via Go backend (which calls Python proxy):
   ```python
   # Go backend handles this internally
   # Client only interacts with Go backend
   ```

3. **Execute queries** through Go backend:
   ```python
   # Client sends to Go backend
   # Go backend validates and forwards to Python proxy if allowed
   ```

### Benefits of This Architecture

✅ **Separation of Concerns**
- Python service focuses on database operations
- Go backend handles business logic and permissions

✅ **Stateless Proxy**
- Python service doesn't need to know about permissions
- Easier to scale and maintain

✅ **Centralized Control**
- All permission logic in one place (Go backend)
- Consistent enforcement across all clients

✅ **Security**
- Python service can't be bypassed for permission checks
- Go backend is the single source of truth

### Migration from Old Permission System

> [!WARNING]
> **Breaking Change**: The `/set-permissions` endpoint has been removed.

**Old approach (deprecated):**
```python
# This no longer works - permissions were managed in Python
requests.post("http://localhost:8000/set-permissions", json={
    "allow_write_operations": True,
    "allow_ddl_operations": False
})
```

**New approach:**
1. Manage permissions in the Go backend database
2. Go backend validates permissions before calling Python proxy
3. Python proxy executes queries without validation

---

## Best Practices

1. **Always specify `db_type`** when generating SQL to ensure database-specific syntax
2. **Use persistent connections** for multiple queries to improve performance
3. **Validate queries** with dry-run before executing on production data
4. **Provide schema context** to generate more accurate SQL
5. **Disconnect** when done to free up database resources
6. **Use HTTPS** in production to protect connection strings
7. **Implement authentication** to control API access
8. **Manage permissions in Go backend** for centralized control
9. **Use appropriate project IDs** to ensure correct permission enforcement

