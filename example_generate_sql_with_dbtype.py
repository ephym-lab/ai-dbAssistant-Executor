#!/usr/bin/env python3
"""
Example: Using db_type parameter in generate-sql endpoint

This demonstrates how the db_type parameter helps generate
database-specific SQL queries.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def print_section(title):
    """Print a section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def generate_and_print(question, db_type=None, db_schema=None):
    """Generate SQL and print the result."""
    request_data = {"question": question}
    
    if db_type:
        request_data["db_type"] = db_type
    if db_schema:
        request_data["db_schema"] = db_schema
    
    print(f"Question: {question}")
    if db_type:
        print(f"Database Type: {db_type}")
    
    response = requests.post(f"{BASE_URL}/generate-sql", json=request_data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nExplanation: {result.get('content')}")
        print(f"\nGenerated SQL:\n{result.get('query')}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

def main():
    print_section("SQL Generation with db_type Parameter")
    
    # Example 1: Generate SQL for PostgreSQL
    print_section("Example 1: PostgreSQL-specific SQL")
    generate_and_print(
        question="Get all users who registered in the last 30 days",
        db_type="postgresql"
    )
    
    # Example 2: Generate SQL for MySQL
    print_section("Example 2: MySQL-specific SQL")
    generate_and_print(
        question="Get all users who registered in the last 30 days",
        db_type="mysql"
    )
    
    # Example 3: With schema context
    print_section("Example 3: With Schema Context")
    schema = """
    Table: users
    - id (integer, primary key)
    - username (varchar)
    - email (varchar)
    - created_at (timestamp)
    - is_active (boolean)
    """
    
    generate_and_print(
        question="Find all active users created this year",
        db_type="postgresql",
        db_schema=schema
    )
    
    # Example 4: Without db_type (generic SQL)
    print_section("Example 4: Generic SQL (no db_type)")
    generate_and_print(
        question="Count total number of orders by customer"
    )
    
    # Example 5: Database-specific features
    print_section("Example 5: PostgreSQL JSON Operations")
    generate_and_print(
        question="Extract the 'name' field from a JSONB column called 'metadata'",
        db_type="postgresql"
    )
    
    print_section("Example 6: MySQL String Functions")
    generate_and_print(
        question="Concatenate first_name and last_name with a space",
        db_type="mysql"
    )
    
    print_section("Examples Complete!")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to the API server.")
        print("Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"\n✗ Error: {e}")
