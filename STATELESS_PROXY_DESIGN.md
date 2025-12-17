# Stateless Proxy Design

## Overview

The DB Assistant API is designed as a **stateless proxy** that relies entirely on explicit connections via the `/connect-db` endpoint. No environment variables are required for database connections.

## Key Design Principles

### 1. No Environment Variables for Connections
- Database connections are **only** established via `/connect-db` endpoint
- Connection details come from request parameters, not environment
- Perfect for proxy servers where the main application manages sessions

### 2. Explicit Connection Required
All database operations require an active connection:
- `/execute-sql` - Requires prior `/connect-db`
- `/validate-sql` - Requires prior `/connect-db`
- `/db-info` - Requires prior `/connect-db`

### 3. Session Management by Main Server
The Python proxy doesn't manage sessions. Your main Go server handles:
- User authentication
- Session tracking
- Connection state management
- When to connect/disconnect

## API Workflow

### Standard Flow

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Connect to database (managed by your Go server)
connect_response = requests.post(f"{BASE_URL}/connect-db", json={
    "db_type": "postgresql",
    "connection_string": "postgresql://user:pass@host:5432/db"
})

# 2. Execute queries (connection is maintained)
execute_response = requests.post(f"{BASE_URL}/execute-sql", json={
    "query": "SELECT * FROM users LIMIT 10"
})

# 3. Disconnect when session ends (managed by your Go server)
disconnect_response = requests.post(f"{BASE_URL}/disconnect-db")
```

### Error Handling

**Without Connection:**
```bash
# Trying to execute without connecting first
curl -X POST http://localhost:8000/execute-sql \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT 1"}'

# Response: 400 Bad Request
{
  "detail": "No database connection. Please connect to a database using /connect-db endpoint first."
}
```

**With Connection:**
```bash
# First connect
curl -X POST http://localhost:8000/connect-db \
  -H "Content-Type: application/json" \
  -d '{
    "db_type": "postgresql",
    "connection_string": "postgresql://user:pass@localhost:5432/mydb"
  }'

# Then execute
curl -X POST http://localhost:8000/execute-sql \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT 1"}'

# Response: 200 OK
{
  "success": true,
  "query_type": "SELECT",
  "columns": ["?column?"],
  "rows": [[1]],
  "row_count": 1
}
```

## Integration with Go Server

### Example Go Integration

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
    ConnString  string
    IsConnected bool
}

var sessions = make(map[string]*Session)

// Connect user to their database
func connectUserDB(sessionID string, dbType string, connString string) error {
    payload := map[string]string{
        "db_type":           dbType,
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
    
    if resp.StatusCode == 200 {
        sessions[sessionID] = &Session{
            DBType:      dbType,
            ConnString:  connString,
            IsConnected: true,
        }
    }
    
    return nil
}

// Execute query for user
func executeQuery(sessionID string, query string) (map[string]interface{}, error) {
    session, exists := sessions[sessionID]
    if !exists || !session.IsConnected {
        return nil, fmt.Errorf("user not connected to database")
    }
    
    payload := map[string]interface{}{
        "query":   query,
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

// Disconnect user
func disconnectUserDB(sessionID string) error {
    resp, err := http.Post(pythonProxyURL+"/disconnect-db", "", nil)
    if err != nil {
        return err
    }
    defer resp.Body.Close()
    
    if session, exists := sessions[sessionID]; exists {
        session.IsConnected = false
    }
    
    return nil
}
```

## Configuration

### Optional Environment Variables

These are **optional** and only affect query execution behavior, not connections:

```bash
# Security settings (optional, defaults to false)
ALLOW_WRITE_OPERATIONS=true
ALLOW_DDL_OPERATIONS=false
MAX_ROWS_RETURNED=1000

# AI service (required for /generate-sql endpoint)
AI_PROVIDER=openai
OPENAI_API_KEY=your_key_here
```

### No Database Connection Variables Needed

These are **NOT** required:
```bash
# ❌ NOT NEEDED
DB_TYPE=postgresql
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=mydb
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword
```

All connection details come from the `/connect-db` request.

## Benefits of Stateless Design

1. **Flexibility**: Each request can connect to different databases
2. **Security**: No credentials stored in environment
3. **Scalability**: Easy to scale horizontally
4. **Session Control**: Main server has full control over connections
5. **Multi-tenancy**: Different users can connect to different databases

## API Endpoints Summary

| Endpoint | Requires Connection | Purpose |
|----------|---------------------|---------|
| `/generate-sql` | ❌ No | Generate SQL from natural language |
| `/connect-db` | ❌ No | Establish database connection |
| `/disconnect-db` | ✅ Yes | Close database connection |
| `/execute-sql` | ✅ Yes | Execute SQL query |
| `/validate-sql` | ✅ Yes | Validate SQL (dry-run) |
| `/db-info` | ✅ Yes | Get connection information |

## Error Responses

### 400 Bad Request
```json
{
  "detail": "No database connection. Please connect to a database using /connect-db endpoint first."
}
```
**Solution**: Call `/connect-db` first

### 403 Forbidden
```json
{
  "detail": "Write operations are disabled. Query type: INSERT"
}
```
**Solution**: Set `ALLOW_WRITE_OPERATIONS=true` or use read-only queries

### 500 Internal Server Error
```json
{
  "detail": "PostgreSQL connection failed: ..."
}
```
**Solution**: Check connection string and database availability

## Best Practices

1. **Connect Once Per Session**: Your Go server should connect when user logs in
2. **Reuse Connection**: Keep connection alive for multiple queries
3. **Disconnect on Logout**: Clean up when user session ends
4. **Handle Errors**: Check connection status before executing queries
5. **Validate Input**: Sanitize connection strings and queries in your Go server
6. **Use HTTPS**: Protect connection strings in transit
7. **Timeout Handling**: Implement timeouts in your Go server for proxy calls

## Complete Example

```python
import requests

BASE_URL = "http://localhost:8000"

# Simulate a user session
def user_session(user_id, db_type, connection_string):
    print(f"Starting session for user: {user_id}")
    
    # 1. Connect
    conn_resp = requests.post(f"{BASE_URL}/connect-db", json={
        "db_type": db_type,
        "connection_string": connection_string
    })
    
    if conn_resp.status_code != 200:
        print("Failed to connect")
        return
    
    print("✓ Connected to database")
    
    # 2. Check connection info
    info_resp = requests.get(f"{BASE_URL}/db-info")
    print(f"✓ Database: {info_resp.json()['database']}")
    
    # 3. Execute queries
    queries = [
        "SELECT COUNT(*) FROM users",
        "SELECT * FROM users LIMIT 5"
    ]
    
    for query in queries:
        exec_resp = requests.post(f"{BASE_URL}/execute-sql", json={
            "query": query
        })
        result = exec_resp.json()
        print(f"✓ Query executed: {result.get('row_count')} rows")
    
    # 4. Disconnect
    disc_resp = requests.post(f"{BASE_URL}/disconnect-db")
    print("✓ Disconnected")

# Run session
user_session(
    user_id="user123",
    db_type="postgresql",
    connection_string="postgresql://user:pass@localhost:5432/mydb"
)
```
