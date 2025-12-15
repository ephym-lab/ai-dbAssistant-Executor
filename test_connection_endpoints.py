#!/usr/bin/env python3
"""
Test script for database connection endpoints.
This script demonstrates how to use the /connect-db and /disconnect-db endpoints.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def print_response(title, response):
    """Pretty print API response."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)

def main():
    print("Testing Database Connection Endpoints")
    print("="*60)
    
    # Example connection strings (update with your actual credentials)
    # PostgreSQL: postgresql://user:password@host:port/database
    # MySQL: mysql://user:password@host:port/database
    connection_string = "postgresql://user:password@localhost:5432/testdb"
    db_type = "postgresql"
    
    print(f"\nUsing connection string: {connection_string}")
    print(f"Database type: {db_type}")
    
    # 1. Check initial DB info
    print("\n1. Checking initial database info...")
    response = requests.get(f"{BASE_URL}/db-info")
    print_response("Initial DB Info", response)
    
    # 2. Connect to database
    print("\n2. Connecting to database...")
    connect_data = {
        "db_type": db_type,
        "connection_string": connection_string
    }
    response = requests.post(f"{BASE_URL}/connect-db", json=connect_data)
    print_response("Connect Database", response)
    
    # 3. Check DB info after connection
    print("\n3. Checking database info after connection...")
    response = requests.get(f"{BASE_URL}/db-info")
    print_response("DB Info (Connected)", response)
    
    # 4. Try connecting again (should show already connected)
    print("\n4. Attempting to connect again...")
    response = requests.post(f"{BASE_URL}/connect-db", json=connect_data)
    print_response("Connect Again", response)
    
    # 5. Execute a query using the persistent connection
    print("\n5. Executing a query with persistent connection...")
    query_data = {
        "query": "SELECT 1 as test",
        "dry_run": False
    }
    response = requests.post(f"{BASE_URL}/execute-sql", json=query_data)
    print_response("Execute Query", response)
    
    # 6. Disconnect from database
    print("\n6. Disconnecting from database...")
    response = requests.post(f"{BASE_URL}/disconnect-db")
    print_response("Disconnect Database", response)
    
    # 7. Check DB info after disconnection
    print("\n7. Checking database info after disconnection...")
    response = requests.get(f"{BASE_URL}/db-info")
    print_response("DB Info (Disconnected)", response)
    
    # 8. Try disconnecting again (should show already disconnected)
    print("\n8. Attempting to disconnect again...")
    response = requests.post(f"{BASE_URL}/disconnect-db")
    print_response("Disconnect Again", response)
    
    print("\n" + "="*60)
    print("Test completed!")
    print("="*60)

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to the API server.")
        print("Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"\nError: {e}")
