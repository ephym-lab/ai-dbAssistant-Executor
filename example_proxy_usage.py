#!/usr/bin/env python3
"""
Example: Using the DB Assistant as a Proxy Service

This example demonstrates how to use the DB Assistant API as a proxy
that accepts connection strings from clients instead of using environment variables.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def print_section(title):
    """Print a section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def print_response(response):
    """Pretty print response."""
    print(f"Status: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)

def main():
    print_section("DB Assistant Proxy Example")
    
    # Scenario: Client sends connection string to connect to their database
    # This could be PostgreSQL, MySQL, etc.
    
    # Example 1: PostgreSQL Database
    print_section("1. Connecting to PostgreSQL Database")
    pg_connection = "postgresql://postgres:password@localhost:5432/testdb"
    
    connect_request = {
        "db_type": "postgresql",
        "connection_string": pg_connection
    }
    
    response = requests.post(f"{BASE_URL}/connect-db", json=connect_request)
    print_response(response)
    
    if response.status_code == 200:
        print("\n✓ Successfully connected to PostgreSQL!")
        
        # Execute a query
        print_section("2. Executing Query on PostgreSQL")
        query_request = {
            "query": "SELECT version() as postgres_version",
            "dry_run": False
        }
        
        response = requests.post(f"{BASE_URL}/execute-sql", json=query_request)
        print_response(response)
        
        # Disconnect
        print_section("3. Disconnecting from PostgreSQL")
        response = requests.post(f"{BASE_URL}/disconnect-db")
        print_response(response)
    
    # Example 2: MySQL Database
    print_section("4. Connecting to MySQL Database")
    mysql_connection = "mysql://root:password@localhost:3306/testdb"
    
    connect_request = {
        "db_type": "mysql",
        "connection_string": mysql_connection
    }
    
    response = requests.post(f"{BASE_URL}/connect-db", json=connect_request)
    print_response(response)
    
    if response.status_code == 200:
        print("\n✓ Successfully connected to MySQL!")
        
        # Execute a query
        print_section("5. Executing Query on MySQL")
        query_request = {
            "query": "SELECT DATABASE() as current_database",
            "dry_run": False
        }
        
        response = requests.post(f"{BASE_URL}/execute-sql", json=query_request)
        print_response(response)
        
        # Disconnect
        print_section("6. Disconnecting from MySQL")
        response = requests.post(f"{BASE_URL}/disconnect-db")
        print_response(response)
    
    # Example 3: Multiple Queries with Persistent Connection
    print_section("7. Multiple Queries with Persistent Connection")
    
    # Connect
    connect_request = {
        "db_type": "postgresql",
        "connection_string": "postgresql://postgres:password@localhost:5432/testdb"
    }
    response = requests.post(f"{BASE_URL}/connect-db", json=connect_request)
    
    if response.status_code == 200:
        # Execute multiple queries
        queries = [
            "SELECT 1 as first_query",
            "SELECT 2 as second_query",
            "SELECT 3 as third_query"
        ]
        
        for i, query in enumerate(queries, 1):
            print(f"\nQuery {i}: {query}")
            query_request = {"query": query, "dry_run": False}
            response = requests.post(f"{BASE_URL}/execute-sql", json=query_request)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print(f"  ✓ Result: {result.get('rows')}")
                else:
                    print(f"  ✗ Error: {result.get('error')}")
        
        # Disconnect
        print("\nDisconnecting...")
        requests.post(f"{BASE_URL}/disconnect-db")
    
    print_section("Example Complete!")
    print("This demonstrates how the API can act as a proxy,")
    print("accepting connection strings from clients dynamically.")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to the API server.")
        print("Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"\n✗ Error: {e}")
