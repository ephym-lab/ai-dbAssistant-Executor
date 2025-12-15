# Database Connection Management Endpoints

This document describes the new database connection management endpoints added to the AI SQL Assistant API.

## Overview

Two new endpoints have been added to allow manual management of database connections:
- `POST /connect-db` - Establish a persistent database connection
- `POST /disconnect-db` - Close the database connection

## Benefits

### Persistent Connection Mode
When you use `/connect-db`, the database connection remains open and is reused across multiple query executions. This provides:
- **Better Performance**: Eliminates connection overhead for each query
- **Connection Pooling**: Maintains a persistent connection that can be reused
- **Manual Control**: You decide when to connect and disconnect

### Temporary Connection Mode (Default)
If you don't explicitly connect using `/connect-db`, the API will automatically:
- Create a temporary connection for each query
- Execute the query
- Close the connection immediately after

## Endpoints

### POST /connect-db

Establishes a persistent connection to the database using a connection string.

**Request:**
```bash
curl -X POST http://localhost:8000/connect-db \
  -H "Content-Type: application/json" \
  -d '{
    "db_type": "postgresql",
    "connection_string": "postgresql://user:password@localhost:5432/mydb"
  }'
```

**Request Body:**
```json
{
  "db_type": "postgresql",
  "connection_string": "postgresql://user:password@localhost:5432/mydb"
}
```

**Parameters:**
- `db_type` (required): Database type - either `"postgresql"` or `"mysql"`
- `connection_string` (required): Database connection string

**Supported Connection String Formats:**
- PostgreSQL: `postgresql://user:password@host:port/database` or `postgres://user:password@host:port/database`
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
  }
}
```

**Response (Already Connected):**
```json
{
  "success": true,
  "message": "Database already connected. Disconnect first to connect to a different database.",
  "connection_info": {
    "type": "PostgreSQL",
    "host": "localhost",
    "port": 5432,
    "database": "mydb",
    "connected": true
  }
}
```

**Response (Invalid Connection String):**
```json
{
  "detail": "Invalid connection string: <error details>"
}
```

### POST /disconnect-db

Closes the database connection.

**Request:**
```bash
curl -X POST http://localhost:8000/disconnect-db
```

**Response (Success):**
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

**Response (Already Disconnected):**
```json
{
  "success": true,
  "message": "Database already disconnected"
}
```

## Usage Examples

### Example 1: Using Persistent Connection

```python
import requests

BASE_URL = "http://localhost:8000"

# Connection details for your database
db_type = "postgresql"
connection_string = "postgresql://myuser:mypassword@localhost:5432/mydb"

# 1. Connect to database
connect_data = {
    "db_type": db_type,
    "connection_string": connection_string
}
response = requests.post(f"{BASE_URL}/connect-db", json=connect_data)
print(response.json())

# 2. Execute multiple queries (reuses the same connection)
for i in range(5):
    query_data = {
        "query": f"SELECT {i} as number",
        "dry_run": False
    }
    response = requests.post(f"{BASE_URL}/execute-sql", json=query_data)
    print(response.json())

# 3. Disconnect when done
response = requests.post(f"{BASE_URL}/disconnect-db")
print(response.json())
```

### Example 2: Using Temporary Connections (Default)

```python
import requests

BASE_URL = "http://localhost:8000"

# Execute query without explicit connection
# (connection is created and closed automatically)
# Note: This still requires DB_TYPE and related env vars to be set
query_data = {
    "query": "SELECT * FROM users LIMIT 10",
    "dry_run": False
}
response = requests.post(f"{BASE_URL}/execute-sql", json=query_data)
print(response.json())
```

### Example 3: Check Connection Status

```python
import requests

BASE_URL = "http://localhost:8000"

# Get database info (shows connection status)
response = requests.get(f"{BASE_URL}/db-info")
print(response.json())
# Output includes "connected": true/false
```

### Example 4: Different Database Types

```python
import requests

BASE_URL = "http://localhost:8000"

# PostgreSQL
pg_connection = "postgresql://user:pass@localhost:5432/mydb"
response = requests.post(f"{BASE_URL}/connect-db", 
                        json={
                            "db_type": "postgresql",
                            "connection_string": pg_connection
                        })

# MySQL
mysql_connection = "mysql://user:pass@localhost:3306/mydb"
response = requests.post(f"{BASE_URL}/connect-db", 
                        json={
                            "db_type": "mysql",
                            "connection_string": mysql_connection
                        })
```

## Testing

A test script is provided to demonstrate the new endpoints:

```bash
# Make sure the API server is running
python test_connection_endpoints.py
```

The test script will:
1. Check initial database info
2. Connect to the database
3. Verify connection status
4. Execute a query using the persistent connection
5. Disconnect from the database
6. Verify disconnection status

## Implementation Details

### Global Connection Management

The API now maintains a global `db_executor` variable that stores the persistent database connection. 

- When `/connect-db` is called with a connection string, it parses the string, creates and stores the executor
- When `/execute-sql` is called:
  - If a persistent connection exists, it uses that
  - Otherwise, it creates a temporary connection for that query only (requires env vars)
- When `/disconnect-db` is called, it closes and clears the global executor

### Connection String Parsing

The `from_connection_string` method parses standard database URIs:
- Extracts scheme (postgresql/mysql), username, password, host, port, and database name
- Creates appropriate executor (PostgreSQL or MySQL) based on the scheme
- Validates the connection string format

### Thread Safety Note

⚠️ **Important**: The current implementation uses a global variable for connection management. In a production environment with multiple workers or threads, you should consider using:
- Connection pooling libraries (e.g., SQLAlchemy)
- Thread-local storage
- Proper locking mechanisms

## Error Handling

Both endpoints handle common error scenarios:

- **Invalid connection string**: Returns 400 error with details about the parsing error
- **Unsupported database type**: Returns 400 error if the scheme is not postgresql/mysql
- **Connection failures**: Returns 500 error with details about the connection failure
- **Already connected/disconnected**: Returns success message indicating current state

## Configuration

### Using Connection Strings (Recommended for Proxy)

The `/connect-db` endpoint accepts connection strings directly as parameters, eliminating the need for environment variables:

**PostgreSQL:**
```
postgresql://user:password@host:port/database
postgres://user:password@host:port/database
```

**MySQL:**
```
mysql://user:password@host:port/database
```

**Example:**
```bash
curl -X POST http://localhost:8000/connect-db \
  -H "Content-Type: application/json" \
  -d '{
    "db_type": "postgresql",
    "connection_string": "postgresql://myuser:mypass@localhost:5432/mydb"
  }'
```

### Using Environment Variables (Optional - For Temporary Connections)

If you don't use `/connect-db` and rely on temporary connections, you'll need to set environment variables:

**PostgreSQL:**
```bash
DB_TYPE=postgresql
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=mydb
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword
```

**MySQL:**
```bash
DB_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DB=mydb
MYSQL_USER=myuser
MYSQL_PASSWORD=mypassword
```

