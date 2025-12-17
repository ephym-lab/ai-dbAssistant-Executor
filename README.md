# AI SQL Assistant - Database Proxy

A stateless Python proxy service that provides AI-powered SQL generation and secure database query execution with dynamic permission management. Perfect for integration with Go (or any) backend servers that need to manage multiple user database connections.

## 🌟 Features

- 🤖 **AI-Powered SQL Generation**: Convert natural language to database-specific SQL using OpenAI or Google Gemini
- 🔌 **Stateless Proxy Design**: No environment variables needed for database connections
- 🔐 **Dynamic Permissions**: Control write and DDL operations per session via API
- 🗄️ **Multi-Database Support**: PostgreSQL and MySQL with database-specific syntax
- 🔒 **Secure by Default**: Read-only permissions, query validation, and row limits
- 📊 **Connection Management**: Persistent connections with explicit connect/disconnect
- 🚀 **FastAPI**: High-performance async API with automatic documentation

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Usage Examples](#usage-examples)
- [Configuration](#configuration)
- [Integration Guide](#integration-guide)
- [Security](#security)
- [Development](#development)

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL or MySQL database (for query execution)
- OpenAI or Google Gemini API key (for SQL generation)

### Installation

1. **Clone and Setup**:
   ```bash
   cd DBAssistantMl
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure Environment** (create `.env` file):
   ```env
   # AI Service (required for /generate-sql endpoint)
   AI_PROVIDER=openai  # or 'gemini'
   OPENAI_API_KEY=sk-your-key-here
   # OR
   GEMINI_API_KEY=your-gemini-key-here
   
   # Optional: Query execution limits
   MAX_ROWS_RETURNED=1000
   ```

3. **Start the Server**:
   ```bash
   cd src
   uvicorn routes.api:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Test the API**:
   ```bash
   curl http://localhost:8000/
   ```

5. **View Interactive Docs**: Visit `http://localhost:8000/docs`

## 📁 Project Structure

```
DBAssistantMl/
├── .env                    # Environment configuration (create from .env.example)
├── .env.example            # Environment template
├── requirements.txt        # Python dependencies
├── README.md              # This file
│
├── src/                   # Source code
│   ├── main.py           # CLI interface (optional)
│   ├── config/           # Configuration
│   │   ├── __init__.py
│   │   └── prompts.py    # AI system prompts
│   ├── schemas/          # Pydantic models
│   │   ├── __init__.py
│   │   └── sql_schemas.py
│   ├── services/         # Business logic
│   │   ├── __init__.py
│   │   ├── ai_service.py     # AI provider abstraction
│   │   └── db_executor.py    # Database executors
│   └── routes/           # API endpoints
│       ├── __init__.py
│       └── api.py        # FastAPI routes
│
├── example_proxy_usage.py          # Example: Proxy usage patterns
├── example_permissions.py          # Example: Permissions management
├── example_generate_sql_with_dbtype.py  # Example: SQL generation
├── test_connection_endpoints.py    # Test script
│
└── Documentation/
    ├── API_DOCUMENTATION.md              # Complete API reference
    ├── STATELESS_PROXY_DESIGN.md        # Architecture guide
    ├── PERMISSIONS_MANAGEMENT.md         # Permissions guide
    └── CONNECTION_STRING_IMPLEMENTATION.md  # Connection details
```

## 🔌 API Endpoints

### SQL Generation

#### `POST /generate-sql`
Generate SQL from natural language using AI.

**Request:**
```json
{
  "question": "Get all users who registered in the last 30 days",
  "db_type": "postgresql",  // optional: "postgresql" or "mysql"
  "db_schema": "users(id, username, email, created_at)"  // optional
}
```

**Response:**
```json
{
  "content": "This query selects users from the last 30 days...",
  "query": "SELECT * FROM users WHERE created_at >= NOW() - INTERVAL '30 days';"
}
```

### Connection Management

#### `POST /connect-db`
Establish a persistent database connection.

**Request:**
```json
{
  "db_type": "postgresql",  // required: "postgresql" or "mysql"
  "connection_string": "postgresql://user:password@host:5432/database"
}
```

**Response:**
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
  }
}
```

#### `POST /disconnect-db`
Close the database connection.

**Response:**
```json
{
  "success": true,
  "message": "Database disconnected successfully",
  "previous_connection": {...}
}
```

#### `GET /db-info`
Get current database connection information (requires active connection).

**Response:**
```json
{
  "type": "PostgreSQL",
  "host": "localhost",
  "port": 5432,
  "database": "mydb",
  "connected": true
}
```

### Query Execution

#### `POST /execute-sql`
Execute a SQL query (requires active connection).

**Request:**
```json
{
  "query": "SELECT * FROM users LIMIT 10",
  "dry_run": false  // optional: true for validation only
}
```

**Response (SELECT):**
```json
{
  "success": true,
  "query_type": "SELECT",
  "columns": ["id", "username", "email"],
  "rows": [[1, "john", "john@example.com"], [2, "jane", "jane@example.com"]],
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

#### `POST /validate-sql`
Validate SQL query without executing (dry-run mode).

**Request:**
```json
{
  "query": "SELECT * FROM users WHERE id = 1"
}
```

### Permissions Management

#### `POST /set-permissions`
Set query execution permissions dynamically.

**Request:**
```json
{
  "allow_write_operations": true,  // INSERT, UPDATE, DELETE
  "allow_ddl_operations": false    // CREATE, DROP, ALTER, TRUNCATE
}
```

**Response:**
```json
{
  "success": true,
  "message": "Permissions updated successfully",
  "permissions": {
    "allow_write_operations": true,
    "allow_ddl_operations": false
  }
}
```

#### `GET /get-permissions`
Get current permission settings.

**Response:**
```json
{
  "allow_write_operations": false,
  "allow_ddl_operations": false
}
```

### Utility Endpoints

- `GET /` - API information and endpoint list
- `GET /health` - Health check

## 💡 Usage Examples

### Example 1: Complete Workflow

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Generate SQL using AI
response = requests.post(f"{BASE_URL}/generate-sql", json={
    "question": "Find all active users",
    "db_type": "postgresql",
    "db_schema": "users(id, username, email, is_active, created_at)"
})
sql_query = response.json()["query"]

# 2. Connect to database
requests.post(f"{BASE_URL}/connect-db", json={
    "db_type": "postgresql",
    "connection_string": "postgresql://user:pass@localhost:5432/mydb"
})

# 3. Set permissions (enable write operations)
requests.post(f"{BASE_URL}/set-permissions", json={
    "allow_write_operations": True,
    "allow_ddl_operations": False
})

# 4. Execute the generated query
result = requests.post(f"{BASE_URL}/execute-sql", json={
    "query": sql_query
})
print(f"Found {result.json()['row_count']} users")

# 5. Disconnect
requests.post(f"{BASE_URL}/disconnect-db")
```

### Example 2: Role-Based Permissions

```python
def setup_user_session(user_role):
    """Set permissions based on user role"""
    permissions = {
        "admin": {"allow_write_operations": True, "allow_ddl_operations": True},
        "editor": {"allow_write_operations": True, "allow_ddl_operations": False},
        "viewer": {"allow_write_operations": False, "allow_ddl_operations": False}
    }
    
    requests.post(f"{BASE_URL}/set-permissions", json=permissions[user_role])
```

### Example 3: Database-Specific SQL

```python
# PostgreSQL-specific query
response = requests.post(f"{BASE_URL}/generate-sql", json={
    "question": "Get JSON field 'name' from metadata column",
    "db_type": "postgresql"
})
# Returns: SELECT metadata->>'name' FROM table;

# MySQL-specific query
response = requests.post(f"{BASE_URL}/generate-sql", json={
    "question": "Get JSON field 'name' from metadata column",
    "db_type": "mysql"
})
# Returns: SELECT JSON_EXTRACT(metadata, '$.name') FROM table;
```

## ⚙️ Configuration

### Environment Variables

#### Required (for SQL generation)
```env
AI_PROVIDER=openai          # or 'gemini'
OPENAI_API_KEY=sk-xxx       # if using OpenAI
GEMINI_API_KEY=xxx          # if using Gemini
```

#### Optional
```env
MAX_ROWS_RETURNED=1000      # Maximum rows for SELECT queries (default: 1000)
```

### Connection Strings

**PostgreSQL:**
```
postgresql://username:password@host:port/database
```

**MySQL:**
```
mysql://username:password@host:port/database
```

### Default Permissions

By default, the API starts in **read-only mode**:
- `allow_write_operations`: `false` (blocks INSERT, UPDATE, DELETE)
- `allow_ddl_operations`: `false` (blocks CREATE, DROP, ALTER, TRUNCATE)

Use `/set-permissions` to enable write or DDL operations as needed.

## 🔗 Integration Guide

### Go Server Integration

```go
package main

import (
    "bytes"
    "encoding/json"
    "net/http"
)

const pythonProxyURL = "http://localhost:8000"

type Session struct {
    UserID      string
    DBType      string
    Connected   bool
    Permissions Permissions
}

type Permissions struct {
    AllowWrite bool `json:"allow_write_operations"`
    AllowDDL   bool `json:"allow_ddl_operations"`
}

// Connect user to their database
func connectUserDB(userID, dbType, connString string) error {
    payload := map[string]string{
        "db_type": dbType,
        "connection_string": connString,
    }
    
    jsonData, _ := json.Marshal(payload)
    resp, err := http.Post(
        pythonProxyURL+"/connect-db",
        "application/json",
        bytes.NewBuffer(jsonData),
    )
    
    if err != nil {
        return err
    }
    defer resp.Body.Close()
    
    // Store session state
    sessions[userID] = &Session{
        UserID: userID,
        DBType: dbType,
        Connected: true,
    }
    
    return nil
}

// Set permissions based on user role
func setUserPermissions(userID, role string) error {
    var perms Permissions
    
    switch role {
    case "admin":
        perms = Permissions{AllowWrite: true, AllowDDL: true}
    case "editor":
        perms = Permissions{AllowWrite: true, AllowDDL: false}
    case "viewer":
        perms = Permissions{AllowWrite: false, AllowDDL: false}
    }
    
    jsonData, _ := json.Marshal(perms)
    resp, err := http.Post(
        pythonProxyURL+"/set-permissions",
        "application/json",
        bytes.NewBuffer(jsonData),
    )
    
    if err != nil {
        return err
    }
    defer resp.Body.Close()
    
    return nil
}

// Execute query
func executeQuery(query string) (map[string]interface{}, error) {
    payload := map[string]interface{}{
        "query": query,
        "dry_run": false,
    }
    
    jsonData, _ := json.Marshal(payload)
    resp, err := http.Post(
        pythonProxyURL+"/execute-sql",
        "application/json",
        bytes.NewBuffer(jsonData),
    )
    
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    
    var result map[string]interface{}
    json.NewDecoder(resp.Body).Decode(&result)
    
    return result, nil
}
```

### Session Management Flow

```
User Login
    ↓
Connect to DB (/connect-db)
    ↓
Set Permissions (/set-permissions)
    ↓
Execute Queries (/execute-sql)
    ↓
User Logout
    ↓
Disconnect (/disconnect-db)
```

## 🔒 Security

### Built-in Security Features

1. **Read-Only by Default**: Both write and DDL permissions start as `false`
2. **Query Validation**: All queries are validated before execution
3. **Row Limits**: SELECT queries are automatically limited (default: 1000 rows)
4. **Connection String Validation**: Validates connection string format
5. **No Credential Storage**: No database credentials stored in environment

### Best Practices

1. **Use HTTPS**: Always use HTTPS in production to protect connection strings
2. **Implement Authentication**: Add authentication to your Go server
3. **Validate Input**: Sanitize connection strings and queries in your main server
4. **Session Timeouts**: Implement timeouts for idle connections
5. **Audit Logging**: Log all connection and query attempts
6. **Rate Limiting**: Implement rate limiting to prevent abuse

### Error Responses

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request (invalid input, not connected) |
| 403 | Forbidden (operation not allowed by permissions) |
| 500 | Internal Server Error (database error, connection failed) |

## 🛠️ Development

### Running Tests

```bash
# Test connection endpoints
python test_connection_endpoints.py

# Test permissions management
python example_permissions.py

# Test proxy usage
python example_proxy_usage.py

# Test SQL generation
python example_generate_sql_with_dbtype.py
```

### Running with Auto-Reload

```bash
cd src
uvicorn routes.api:app --host 0.0.0.0 --port 8000 --reload
```

### API Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation.

## 📚 Additional Documentation

- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Complete API reference
- **[STATELESS_PROXY_DESIGN.md](STATELESS_PROXY_DESIGN.md)** - Architecture and design patterns
- **[PERMISSIONS_MANAGEMENT.md](PERMISSIONS_MANAGEMENT.md)** - Detailed permissions guide
- **[CONNECTION_STRING_IMPLEMENTATION.md](CONNECTION_STRING_IMPLEMENTATION.md)** - Connection details

## 🤝 Contributing

This is a proxy service designed to work with your main Go server. Customize as needed for your use case.

## 📝 License

[Your License Here]

## 🆘 Troubleshooting

### Common Issues

**"No database connection" error**
- Make sure to call `/connect-db` before executing queries

**"Write operations are disabled" error**
- Call `/set-permissions` with `allow_write_operations: true`

**"Database not configured" error**
- Check your connection string format
- Verify database is accessible

**AI generation not working**
- Verify `AI_PROVIDER` is set in `.env`
- Check that your API key is valid

### Getting Help

Check the example scripts in the root directory for working code samples.

---

**Built with ❤️ for seamless database proxy integration**
