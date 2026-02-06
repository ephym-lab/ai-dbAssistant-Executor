"""
Example usage of the context-aware database assistant.

This demonstrates:
1. Using project_id for schema retrieval from Qdrant
2. Handling different decision types (EXECUTE, INVALID, EXPLAIN)
3. Working with suggestions for invalid requests
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def example_valid_request():
    """Example: Valid request with schema context."""
    print("\n" + "="*60)
    print("Example 1: Valid Request with Schema Context")
    print("="*60)
    
    payload = {
        "question": "Show me all active users who registered in the last month",
        "project_id": "my-project-123",
        "db_type": "postgresql"
    }
    
    response = requests.post(f"{BASE_URL}/generate-sql", json=payload)
    result = response.json()
    
    print(f"\nDecision: {result['decision']}")
    print(f"Explanation: {result['content']}")
    
    if result['decision'] == 'EXECUTE':
        print(f"\nGenerated SQL:")
        print(result['query'])
    
    return result

def example_invalid_request():
    """Example: Invalid request (table doesn't exist)."""
    print("\n" + "="*60)
    print("Example 2: Invalid Request - Table Doesn't Exist")
    print("="*60)
    
    payload = {
        "question": "Get all records from the customers table",
        "project_id": "my-project-123",
        "db_type": "postgresql"
    }
    
    response = requests.post(f"{BASE_URL}/generate-sql", json=payload)
    result = response.json()
    
    print(f"\nDecision: {result['decision']}")
    print(f"Explanation: {result['content']}")
    
    if result['decision'] == 'INVALID':
        print(f"\nSuggestions:")
        for i, suggestion in enumerate(result.get('suggestions', []), 1):
            print(f"  {i}. {suggestion}")
    
    return result

def example_column_mismatch():
    """Example: Invalid request (column doesn't exist)."""
    print("\n" + "="*60)
    print("Example 3: Invalid Request - Column Doesn't Exist")
    print("="*60)
    
    payload = {
        "question": "Sort users by registration_date",
        "project_id": "my-project-123",
        "db_type": "postgresql"
    }
    
    response = requests.post(f"{BASE_URL}/generate-sql", json=payload)
    result = response.json()
    
    print(f"\nDecision: {result['decision']}")
    print(f"Explanation: {result['content']}")
    
    if result['decision'] == 'INVALID':
        print(f"\nSuggestions:")
        for i, suggestion in enumerate(result.get('suggestions', []), 1):
            print(f"  {i}. {suggestion}")
    
    return result

def example_explanation_request():
    """Example: Explanation-only request."""
    print("\n" + "="*60)
    print("Example 4: Explanation Request")
    print("="*60)
    
    payload = {
        "question": "What is the difference between INNER JOIN and LEFT JOIN?",
        "db_type": "postgresql"
    }
    
    response = requests.post(f"{BASE_URL}/generate-sql", json=payload)
    result = response.json()
    
    print(f"\nDecision: {result['decision']}")
    print(f"Explanation: {result['content']}")
    
    return result

def example_legacy_mode():
    """Example: Legacy mode without project_id."""
    print("\n" + "="*60)
    print("Example 5: Legacy Mode (No Project ID)")
    print("="*60)
    
    payload = {
        "question": "Get all users",
        "db_type": "postgresql",
        "db_schema": "users(id, username, email, created_at, is_active)"
    }
    
    response = requests.post(f"{BASE_URL}/generate-sql", json=payload)
    result = response.json()
    
    print(f"\nDecision: {result['decision']}")
    print(f"Explanation: {result['content']}")
    
    if result['decision'] == 'EXECUTE':
        print(f"\nGenerated SQL:")
        print(result['query'])
    
    return result

def example_workflow():
    """Example: Complete workflow with error handling."""
    print("\n" + "="*60)
    print("Example 6: Complete Workflow with Error Handling")
    print("="*60)
    
    # Step 1: Try to query a table
    print("\nStep 1: Attempting to query 'orders' table...")
    
    payload = {
        "question": "Get all orders from last week",
        "project_id": "my-project-123",
        "db_type": "postgresql"
    }
    
    response = requests.post(f"{BASE_URL}/generate-sql", json=payload)
    result = response.json()
    
    if result['decision'] == 'INVALID':
        print(f"❌ Request invalid: {result['content']}")
        print(f"\n💡 Suggestions:")
        for suggestion in result.get('suggestions', []):
            print(f"   - {suggestion}")
        
        # Step 2: Use suggestion to fix the request
        print("\nStep 2: Using suggestion to fix the request...")
        # (In a real app, you might parse the suggestion or ask the user)
        
    elif result['decision'] == 'EXECUTE':
        print(f"✅ SQL generated successfully!")
        print(f"\nSQL Query:")
        print(result['query'])
        
        # Step 3: Execute the query (if connected to DB)
        print("\nStep 3: Ready to execute query...")
        # execute_response = requests.post(f"{BASE_URL}/execute-sql", json={"query": result['query']})
    
    return result

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  CONTEXT-AWARE DATABASE ASSISTANT - USAGE EXAMPLES")
    print("="*60)
    
    # Run all examples
    example_valid_request()
    example_invalid_request()
    example_column_mismatch()
    example_explanation_request()
    example_legacy_mode()
    example_workflow()
    
    print("\n" + "="*60)
    print("  Examples completed!")
    print("="*60 + "\n")
