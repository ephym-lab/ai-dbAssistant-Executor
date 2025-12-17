"""
Test script for Go backend permissions integration.

This script demonstrates how to:
1. Connect to a database with a project_id
2. Execute queries with permissions fetched from Go backend
3. Handle permission errors
"""

import requests
import json

BASE_URL = "http://localhost:8000"
GO_BACKEND_URL = "http://localhost:8080"

def test_go_backend_permissions():
    """Test the complete workflow with Go backend permissions."""
    
    print("=" * 60)
    print("Testing Go Backend Permissions Integration")
    print("=" * 60)
    
    # Configuration
    project_id = 12  # Change this to your actual project ID
    db_type = "postgresql"
    connection_string = "postgresql://dbassistanttest_user:gQpD9CGdyNPDbvOPTjCixyFBjrd1HtgC@dpg-d4vtr4fpm1nc73bvtelg-a.oregon-postgres.render.com/dbassistanttest"
    
    # Step 1: Connect to database with project_id
    print("\n1. Connecting to database with project_id...")
    try:
        connect_response = requests.post(
            f"{BASE_URL}/connect-db",
            json={
                "db_type": db_type,
                "connection_string": connection_string,
                "project_id": project_id
            }
        )
        
        if connect_response.status_code == 200:
            result = connect_response.json()
            print(f"✓ Connected successfully")
            print(f"  Project ID: {result.get('project_id')}")
            print(f"  Database: {result['connection_info']['database']}")
        else:
            print(f"✗ Connection failed: {connect_response.json()}")
            return
            
    except Exception as e:
        print(f"✗ Error connecting: {e}")
        return
    
    # Step 2: Test SELECT query (should work if allow_read is true)
    print("\n2. Testing SELECT query...")
    try:
        execute_response = requests.post(
            f"{BASE_URL}/execute-sql",
            json={
                "query": "SELECT * FROM users LIMIT 5",
                "dry_run": False
            }
        )
        
        if execute_response.status_code == 200:
            result = execute_response.json()
            print(f"✓ SELECT query executed successfully")
            print(f"  Rows returned: {result.get('row_count', 0)}")
        elif execute_response.status_code == 403:
            print(f"✗ Permission denied: {execute_response.json()['detail']}")
        else:
            print(f"✗ Query failed: {execute_response.json()}")
            
    except Exception as e:
        print(f"✗ Error executing SELECT: {e}")
    
    # Step 3: Test INSERT query (requires allow_write permission)
    print("\n3. Testing INSERT query...")
    try:
        execute_response = requests.post(
            f"{BASE_URL}/execute-sql",
            json={
                "query": "INSERT INTO users (username, email) VALUES ('test', 'test@example.com')",
                "dry_run": False
            }
        )
        
        if execute_response.status_code == 200:
            result = execute_response.json()
            print(f"✓ INSERT query executed successfully")
            print(f"  Affected rows: {result.get('affected_rows', 0)}")
        elif execute_response.status_code == 403:
            print(f"✗ Permission denied: {execute_response.json()['detail']}")
            print(f"  This is expected if allow_write is false in Go backend")
        else:
            print(f"✗ Query failed: {execute_response.json()}")
            
    except Exception as e:
        print(f"✗ Error executing INSERT: {e}")
    
    # Step 4: Test DELETE query (requires allow_delete permission)
    print("\n4. Testing DELETE query...")
    try:
        execute_response = requests.post(
            f"{BASE_URL}/execute-sql",
            json={
                "query": "DELETE FROM users WHERE username = 'test'",
                "dry_run": False
            }
        )
        
        if execute_response.status_code == 200:
            result = execute_response.json()
            print(f"✓ DELETE query executed successfully")
            print(f"  Affected rows: {result.get('affected_rows', 0)}")
        elif execute_response.status_code == 403:
            print(f"✗ Permission denied: {execute_response.json()['detail']}")
            print(f"  This is expected if allow_delete is false in Go backend")
        else:
            print(f"✗ Query failed: {execute_response.json()}")
            
    except Exception as e:
        print(f"✗ Error executing DELETE: {e}")
    
    # Step 5: Test DDL query (requires allow_ddl permission)
    print("\n5. Testing DDL query...")
    try:
        execute_response = requests.post(
            f"{BASE_URL}/execute-sql",
            json={
                "query": "CREATE TABLE test_table (id INT PRIMARY KEY)",
                "dry_run": False
            }
        )
        
        if execute_response.status_code == 200:
            result = execute_response.json()
            print(f"✓ DDL query executed successfully")
        elif execute_response.status_code == 403:
            print(f"✗ Permission denied: {execute_response.json()['detail']}")
            print(f"  This is expected if allow_ddl is false in Go backend")
        else:
            print(f"✗ Query failed: {execute_response.json()}")
            
    except Exception as e:
        print(f"✗ Error executing DDL: {e}")
    
    # Step 6: Disconnect
    print("\n6. Disconnecting from database...")
    try:
        disconnect_response = requests.post(f"{BASE_URL}/disconnect-db")
        
        if disconnect_response.status_code == 200:
            print(f"✓ Disconnected successfully")
        else:
            print(f"✗ Disconnect failed: {disconnect_response.json()}")
            
    except Exception as e:
        print(f"✗ Error disconnecting: {e}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


def test_permission_fetch_directly():
    """Test fetching permissions directly from Go backend."""
    
    print("\n" + "=" * 60)
    print("Testing Direct Permission Fetch from Go Backend")
    print("=" * 60)
    
    project_id = 1  # Change this to your actual project ID
    
    try:
        response = requests.get(
            f"{GO_BACKEND_URL}/api/projects/{project_id}/permissions"
        )
        
        if response.status_code == 200:
            permissions = response.json()
            print(f"\n✓ Successfully fetched permissions for project {project_id}:")
            print(f"  allow_read: {permissions.get('allow_read')}")
            print(f"  allow_write: {permissions.get('allow_write')}")
            print(f"  allow_delete: {permissions.get('allow_delete')}")
            print(f"  allow_ddl: {permissions.get('allow_ddl')}")
        else:
            print(f"\n✗ Failed to fetch permissions: {response.status_code}")
            print(f"  Response: {response.text}")
            
    except Exception as e:
        print(f"\n✗ Error fetching permissions: {e}")
        print(f"  Make sure Go backend is running at {GO_BACKEND_URL}")


if __name__ == "__main__":
    # First test direct permission fetch
    test_permission_fetch_directly()
    
    # Then test full workflow
    print("\n")
    test_go_backend_permissions()
