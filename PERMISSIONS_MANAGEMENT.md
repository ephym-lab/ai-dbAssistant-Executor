# Permissions Management Endpoints

## Overview

Added endpoints to dynamically control write and DDL operation permissions without requiring environment variables or server restarts.

## New Endpoints

### POST /set-permissions

Set permissions for query execution.

**Request:**
```bash
curl -X POST http://localhost:8000/set-permissions \
  -H "Content-Type: application/json" \
  -d '{
    "allow_write_operations": true,
    "allow_ddl_operations": false
  }'
```

**Request Body:**
```json
{
  "allow_write_operations": true,
  "allow_ddl_operations": false
}
```

**Parameters:**
- `allow_write_operations` (boolean): Allow INSERT, UPDATE, DELETE operations (default: false)
- `allow_ddl_operations` (boolean): Allow CREATE, DROP, ALTER, TRUNCATE operations (default: false)

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

### GET /get-permissions

Get current query execution permissions.

**Request:**
```bash
curl http://localhost:8000/get-permissions
```

**Response:**
```json
{
  "allow_write_operations": true,
  "allow_ddl_operations": false
}
```

## Usage Examples

### Example 1: Enable Write Operations

```python
import requests

BASE_URL = "http://localhost:8000"

# Enable write operations
response = requests.post(f"{BASE_URL}/set-permissions", json={
    "allow_write_operations": True,
    "allow_ddl_operations": False
})

print(response.json())
# Output: {"success": true, "message": "Permissions updated successfully", ...}

# Now INSERT/UPDATE/DELETE will work
execute_response = requests.post(f"{BASE_URL}/execute-sql", json={
    "query": "INSERT INTO users (name, email) VALUES ('John', 'john@example.com')"
})
```

### Example 2: Enable DDL Operations

```python
import requests

BASE_URL = "http://localhost:8000"

# Enable DDL operations
response = requests.post(f"{BASE_URL}/set-permissions", json={
    "allow_write_operations": False,
    "allow_ddl_operations": True
})

# Now CREATE/DROP/ALTER will work
execute_response = requests.post(f"{BASE_URL}/execute-sql", json={
    "query": "CREATE TABLE test (id INT, name VARCHAR(100))"
})
```

### Example 3: Check Current Permissions

```python
import requests

BASE_URL = "http://localhost:8000"

# Check current permissions
response = requests.get(f"{BASE_URL}/get-permissions")
permissions = response.json()

print(f"Write operations: {permissions['allow_write_operations']}")
print(f"DDL operations: {permissions['allow_ddl_operations']}")
```

### Example 4: Session-Based Permissions (Go Server)

```go
// User login - set permissions based on user role
func handleUserLogin(userID string, role string) {
    // Connect to database
    connectToDB(userCredentials)
    
    // Set permissions based on role
    permissions := PermissionsRequest{
        AllowWriteOperations: role == "admin" || role == "editor",
        AllowDDLOperations:   role == "admin",
    }
    
    setPermissions(permissions)
    
    // Store session
    sessions[userID] = &Session{
        Connected: true,
        Permissions: permissions,
    }
}
```

## Integration with Go Server

Your Go server can control permissions per user session:

```go
package main

import (
    "bytes"
    "encoding/json"
    "net/http"
)

const pythonProxyURL = "http://localhost:8000"

type PermissionsRequest struct {
    AllowWriteOperations bool `json:"allow_write_operations"`
    AllowDDLOperations   bool `json:"allow_ddl_operations"`
}

// Set permissions for current session
func setPermissions(perms PermissionsRequest) error {
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

// Get current permissions
func getPermissions() (PermissionsRequest, error) {
    resp, err := http.Get(pythonProxyURL + "/get-permissions")
    if err != nil {
        return PermissionsRequest{}, err
    }
    defer resp.Body.Close()
    
    var perms PermissionsRequest
    json.NewDecoder(resp.Body).Decode(&perms)
    
    return perms, nil
}

// Example: Set permissions based on user role
func setupUserSession(userRole string) {
    var perms PermissionsRequest
    
    switch userRole {
    case "admin":
        perms = PermissionsRequest{
            AllowWriteOperations: true,
            AllowDDLOperations:   true,
        }
    case "editor":
        perms = PermissionsRequest{
            AllowWriteOperations: true,
            AllowDDLOperations:   false,
        }
    case "viewer":
        perms = PermissionsRequest{
            AllowWriteOperations: false,
            AllowDDLOperations:   false,
        }
    }
    
    setPermissions(perms)
}
```

## Complete Workflow

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Connect to database
requests.post(f"{BASE_URL}/connect-db", json={
    "db_type": "postgresql",
    "connection_string": "postgresql://user:pass@localhost:5432/db"
})

# 2. Set permissions (e.g., for an admin user)
requests.post(f"{BASE_URL}/set-permissions", json={
    "allow_write_operations": True,
    "allow_ddl_operations": True
})

# 3. Execute write operations
requests.post(f"{BASE_URL}/execute-sql", json={
    "query": "INSERT INTO users (name) VALUES ('Alice')"
})

# 4. Execute DDL operations
requests.post(f"{BASE_URL}/execute-sql", json={
    "query": "CREATE INDEX idx_users_name ON users(name)"
})

# 5. Change permissions (e.g., downgrade to read-only)
requests.post(f"{BASE_URL}/set-permissions", json={
    "allow_write_operations": False,
    "allow_ddl_operations": False
})

# 6. Now write operations will fail
response = requests.post(f"{BASE_URL}/execute-sql", json={
    "query": "DELETE FROM users WHERE id = 1"
})
# Response: 403 Forbidden - "Write operations are disabled"

# 7. Disconnect
requests.post(f"{BASE_URL}/disconnect-db")
```

## Error Handling

### Attempting Write Operation Without Permission

```bash
# Set read-only permissions
curl -X POST http://localhost:8000/set-permissions \
  -H "Content-Type: application/json" \
  -d '{"allow_write_operations": false, "allow_ddl_operations": false}'

# Try to insert
curl -X POST http://localhost:8000/execute-sql \
  -H "Content-Type: application/json" \
  -d '{"query": "INSERT INTO users (name) VALUES (\"test\")"}'

# Response: 403 Forbidden
{
  "detail": "Write operations are disabled. Query type: INSERT"
}
```

### Attempting DDL Operation Without Permission

```bash
# Disable DDL
curl -X POST http://localhost:8000/set-permissions \
  -H "Content-Type: application/json" \
  -d '{"allow_write_operations": true, "allow_ddl_operations": false}'

# Try to create table
curl -X POST http://localhost:8000/execute-sql \
  -H "Content-Type: application/json" \
  -d '{"query": "CREATE TABLE test (id INT)"}'

# Response: 403 Forbidden
{
  "detail": "DDL operations are disabled. Query type: DDL"
}
```

## Benefits

1. **Dynamic Control**: Change permissions without restarting server
2. **Session-Based**: Different permissions for different users
3. **No Environment Variables**: All configuration via API
4. **Fine-Grained**: Separate control for write and DDL operations
5. **Secure**: Default is read-only (both permissions false by default)

## Default Behavior

By default, both permissions are **disabled** (false):
- `allow_write_operations`: false (INSERT, UPDATE, DELETE blocked)
- `allow_ddl_operations`: false (CREATE, DROP, ALTER, TRUNCATE blocked)

This ensures a secure default where only SELECT queries are allowed.

## API Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/set-permissions` | POST | Set write and DDL permissions |
| `/get-permissions` | GET | Get current permissions |
| `/execute-sql` | POST | Execute query (respects permissions) |
| `/validate-sql` | POST | Validate query (respects permissions) |

## Testing

```bash
# Start server (if not running)
cd src
uvicorn routes.api:app --host 0.0.0.0 --port 8000 --reload

# Test permissions
curl http://localhost:8000/get-permissions

# Enable write operations
curl -X POST http://localhost:8000/set-permissions \
  -H "Content-Type: application/json" \
  -d '{"allow_write_operations": true, "allow_ddl_operations": false}'

# Verify
curl http://localhost:8000/get-permissions
```
