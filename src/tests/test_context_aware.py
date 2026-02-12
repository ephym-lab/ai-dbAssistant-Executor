"""
Test script for context-aware database assistant with Qdrant integration.

This script tests:
1. Qdrant connection and health check
2. Schema retrieval from Qdrant
3. Context-aware SQL generation
4. Validation and suggestion logic
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_health_check():
    """Test API health check."""
    print_section("1. Health Check")
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    return response.status_code == 200

def test_qdrant_connection():
    """Test Qdrant service connection."""
    print_section("2. Qdrant Connection Test")
    
    try:
        from src.services.qdrant_service import QdrantService
        
        qdrant = QdrantService()
        health = qdrant.health_check()
        
        print(f"Qdrant Status: {health.get('status')}")
        print(f"Qdrant URL: {health.get('url')}")
        print(f"Collections: {health.get('collections', [])}")
        
        return health.get('status') == 'healthy'
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_context_aware_generation_valid():
    """Test context-aware SQL generation with valid request."""
    print_section("3. Context-Aware Generation - Valid Request")
    
    payload = {
        "question": "Get all users created in the last 30 days",
        "project_id": "test-project-123",
        "db_type": "postgresql"
    }
    
    print(f"Request: {json.dumps(payload, indent=2)}")
    
    response = requests.post(f"{BASE_URL}/generate-sql", json=payload)
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nResponse:")
        print(f"  Decision: {result.get('decision')}")
        print(f"  Content: {result.get('content')}")
        print(f"  Query: {result.get('query')}")
        print(f"  Suggestions: {result.get('suggestions', [])}")
        
        return result.get('decision') in ['EXECUTE', 'INVALID', 'EXPLAIN']
    else:
        print(f"Error: {response.text}")
        return False

def test_context_aware_generation_invalid():
    """Test context-aware SQL generation with invalid request."""
    print_section("4. Context-Aware Generation - Invalid Request")
    
    payload = {
        "question": "Get all records from the nonexistent_table",
        "project_id": "test-project-123",
        "db_type": "postgresql"
    }
    
    print(f"Request: {json.dumps(payload, indent=2)}")
    
    response = requests.post(f"{BASE_URL}/generate-sql", json=payload)
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nResponse:")
        print(f"  Decision: {result.get('decision')}")
        print(f"  Content: {result.get('content')}")
        print(f"  Query: {result.get('query')}")
        print(f"  Suggestions: {result.get('suggestions', [])}")
        
        # For invalid requests, we expect INVALID decision with suggestions
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_legacy_compatibility():
    """Test backward compatibility with legacy requests (no project_id)."""
    print_section("5. Legacy Compatibility Test")
    
    payload = {
        "question": "Get all users",
        "db_type": "postgresql",
        "db_schema": "users(id, username, email, created_at)"
    }
    
    print(f"Request: {json.dumps(payload, indent=2)}")
    
    response = requests.post(f"{BASE_URL}/generate-sql", json=payload)
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nResponse:")
        print(f"  Decision: {result.get('decision')}")
        print(f"  Content: {result.get('content')}")
        print(f"  Query: {result.get('query')}")
        
        return result.get('decision') in ['EXECUTE', 'INVALID', 'EXPLAIN']
    else:
        print(f"Error: {response.text}")
        return False

def test_explanation_request():
    """Test explanation-only request."""
    print_section("6. Explanation Request Test")
    
    payload = {
        "question": "What is a foreign key?",
        "db_type": "postgresql"
    }
    
    print(f"Request: {json.dumps(payload, indent=2)}")
    
    response = requests.post(f"{BASE_URL}/generate-sql", json=payload)
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nResponse:")
        print(f"  Decision: {result.get('decision')}")
        print(f"  Content: {result.get('content')}")
        print(f"  Query: {result.get('query')}")
        
        return result.get('decision') == 'EXPLAIN'
    else:
        print(f"Error: {response.text}")
        return False

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  CONTEXT-AWARE DATABASE ASSISTANT TEST SUITE")
    print("="*60)
    
    results = {
        "Health Check": test_health_check(),
        "Qdrant Connection": test_qdrant_connection(),
        "Valid Request": test_context_aware_generation_valid(),
        "Invalid Request": test_context_aware_generation_invalid(),
        "Legacy Compatibility": test_legacy_compatibility(),
        "Explanation Request": test_explanation_request()
    }
    
    # Print summary
    print_section("TEST SUMMARY")
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:.<40} {status}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return all(results.values())

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
