#!/usr/bin/env python3
"""
Example: Testing Permissions Management

This script demonstrates how to use the /set-permissions endpoint
to control write and DDL operations dynamically.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def print_section(title):
    """Print a section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def print_response(title, response):
    """Pretty print response."""
    print(f"{title}:")
    print(f"Status: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)

def main():
    print_section("Permissions Management Example")
    
    # Connect to database first
    print_section("1. Connecting to Database")
    connect_resp = requests.post(f"{BASE_URL}/connect-db", json={
        "db_type": "postgresql",
        "connection_string": "postgresql://user:password@localhost:5432/testdb"
    })
    print_response("Connection", connect_resp)
    
    if connect_resp.status_code != 200:
        print("\n❌ Failed to connect. Exiting.")
        return
    
    # Check default permissions
    print_section("2. Check Default Permissions")
    perms_resp = requests.get(f"{BASE_URL}/get-permissions")
    print_response("Default Permissions", perms_resp)
    
    # Try write operation (should fail)
    print_section("3. Try INSERT Without Permission")
    insert_resp = requests.post(f"{BASE_URL}/execute-sql", json={
        "query": "INSERT INTO users (name) VALUES ('test')"
    })
    print_response("INSERT Result", insert_resp)
    
    # Enable write operations
    print_section("4. Enable Write Operations")
    set_perms_resp = requests.post(f"{BASE_URL}/set-permissions", json={
        "allow_write_operations": True,
        "allow_ddl_operations": False
    })
    print_response("Set Permissions", set_perms_resp)
    
    # Try write operation again (should work)
    print_section("5. Try INSERT With Permission")
    insert_resp = requests.post(f"{BASE_URL}/execute-sql", json={
        "query": "INSERT INTO users (name) VALUES ('test')"
    })
    print_response("INSERT Result", insert_resp)
    
    # Try DDL operation (should fail)
    print_section("6. Try CREATE TABLE Without Permission")
    create_resp = requests.post(f"{BASE_URL}/execute-sql", json={
        "query": "CREATE TABLE test (id INT)"
    })
    print_response("CREATE Result", create_resp)
    
    # Enable DDL operations
    print_section("7. Enable DDL Operations")
    set_perms_resp = requests.post(f"{BASE_URL}/set-permissions", json={
        "allow_write_operations": True,
        "allow_ddl_operations": True
    })
    print_response("Set Permissions", set_perms_resp)
    
    # Try DDL operation again (should work)
    print_section("8. Try CREATE TABLE With Permission")
    create_resp = requests.post(f"{BASE_URL}/execute-sql", json={
        "query": "CREATE TABLE test (id INT)"
    })
    print_response("CREATE Result", create_resp)
    
    # Disable all write operations
    print_section("9. Disable All Write Operations")
    set_perms_resp = requests.post(f"{BASE_URL}/set-permissions", json={
        "allow_write_operations": False,
        "allow_ddl_operations": False
    })
    print_response("Set Permissions", set_perms_resp)
    
    # SELECT should still work
    print_section("10. SELECT Query (Always Allowed)")
    select_resp = requests.post(f"{BASE_URL}/execute-sql", json={
        "query": "SELECT 1 as test"
    })
    print_response("SELECT Result", select_resp)
    
    # Disconnect
    print_section("11. Disconnecting")
    disconnect_resp = requests.post(f"{BASE_URL}/disconnect-db")
    print_response("Disconnect", disconnect_resp)
    
    print_section("Example Complete!")
    print("Summary:")
    print("- Default permissions: read-only (write=false, ddl=false)")
    print("- Permissions can be changed dynamically via /set-permissions")
    print("- SELECT queries always work regardless of permissions")
    print("- Write operations require allow_write_operations=true")
    print("- DDL operations require allow_ddl_operations=true")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to the API server.")
        print("Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"\n✗ Error: {e}")
