"""
Example: Ingesting database schema into Qdrant

This script demonstrates how to:
1. Connect to a database
2. Extract the schema
3. Ingest it into Qdrant for context-aware SQL generation
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def ingest_schema_example():
    """Example: Ingest database schema into Qdrant."""
    print("\n" + "="*60)
    print("  Schema Ingestion Example")
    print("="*60)
    
    # Configuration
    payload = {
        "project_id": "11",
        "db_type": "postgresql",
        "connection_string": "",
        "clear_existing": True  # Clear any existing schema for this project
    }
    
    print(f"\nIngesting schema for project: {payload['project_id']}")
    print(f"Database: {payload['db_type']}")
    print(f"Clear existing: {payload['clear_existing']}")
    
    # Call the ingest endpoint
    response = requests.post(f"{BASE_URL}/ingest-schema", json=payload)
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        if result['success']:
            print(f"\n✅ Success!")
            print(f"   Project ID: {result['project_id']}")
            print(f"   Tables Ingested: {result['tables_ingested']}")
            print(f"   Message: {result['message']}")
        else:
            print(f"\n❌ Failed!")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            print(f"   Message: {result['message']}")
    else:
        print(f"\n❌ HTTP Error: {response.text}")
    
    return response

def test_context_aware_after_ingestion():
    """Test context-aware SQL generation after schema ingestion."""
    print("\n" + "="*60)
    print("  Testing Context-Aware Generation")
    print("="*60)
    
    payload = {
        "question": "Get all active users who registered in the last month",
        "project_id": "my-project-123",
        "db_type": "postgresql"
    }
    
    print(f"\nQuestion: {payload['question']}")
    print(f"Project ID: {payload['project_id']}")
    
    response = requests.post(f"{BASE_URL}/generate-sql", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"\nDecision: {result['decision']}")
        print(f"Explanation: {result['content']}")
        
        if result['decision'] == 'EXECUTE':
            print(f"\n✅ Generated SQL:")
            print(result['query'])
        elif result['decision'] == 'INVALID':
            print(f"\n❌ Invalid Request")
            print("Suggestions:")
            for i, suggestion in enumerate(result.get('suggestions', []), 1):
                print(f"  {i}. {suggestion}")
    else:
        print(f"\n❌ Error: {response.text}")

def complete_workflow():
    """Complete workflow: Ingest schema then use it."""
    print("\n" + "="*60)
    print("  COMPLETE WORKFLOW: INGEST → GENERATE")
    print("="*60)
    
    # Step 1: Ingest schema
    print("\n📥 Step 1: Ingesting database schema...")
    ingest_payload = {
        "project_id": "ecommerce-app",
        "db_type": "postgresql",
        "connection_string": "postgresql://user:password@localhost:5432/ecommerce",
        "clear_existing": True
    }
    
    ingest_response = requests.post(f"{BASE_URL}/ingest-schema", json=ingest_payload)
    
    if ingest_response.status_code == 200:
        result = ingest_response.json()
        if result['success']:
            print(f"   ✅ Ingested {result['tables_ingested']} tables")
        else:
            print(f"   ❌ Ingestion failed: {result.get('error')}")
            return
    else:
        print(f"   ❌ HTTP Error: {ingest_response.text}")
        return
    
    # Step 2: Generate SQL with context
    print("\n🤖 Step 2: Generating context-aware SQL...")
    
    questions = [
        "Show me all orders from the last week",
        "Get customers who haven't placed an order",
        "Find products that are out of stock"
    ]
    
    for question in questions:
        print(f"\n   Question: {question}")
        
        gen_payload = {
            "question": question,
            "project_id": "ecommerce-app",
            "db_type": "postgresql"
        }
        
        gen_response = requests.post(f"{BASE_URL}/generate-sql", json=gen_payload)
        
        if gen_response.status_code == 200:
            result = gen_response.json()
            
            if result['decision'] == 'EXECUTE':
                print(f"   ✅ {result['decision']}")
                print(f"   SQL: {result['query'][:80]}...")
            elif result['decision'] == 'INVALID':
                print(f"   ❌ {result['decision']}: {result['content']}")
            else:
                print(f"   ℹ️  {result['decision']}: {result['content']}")
        else:
            print(f"   ❌ Error: {gen_response.text}")

def update_schema_example():
    """Example: Update existing schema (clear and re-ingest)."""
    print("\n" + "="*60)
    print("  Schema Update Example")
    print("="*60)
    
    payload = {
        "project_id": "my-project-123",
        "db_type": "postgresql",
        "connection_string": "postgresql://user:password@localhost:5432/mydb",
        "clear_existing": True  # This will delete old schema first
    }
    
    print("\n🔄 Updating schema (clearing existing data)...")
    
    response = requests.post(f"{BASE_URL}/ingest-schema", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            print(f"✅ Schema updated successfully!")
            print(f"   Tables: {result['tables_ingested']}")
        else:
            print(f"❌ Update failed: {result.get('error')}")
    else:
        print(f"❌ HTTP Error: {response.text}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  SCHEMA INGESTION EXAMPLES")
    print("="*60)
    
    # Choose which example to run
    print("\nAvailable examples:")
    print("1. Basic schema ingestion")
    print("2. Test context-aware generation after ingestion")
    print("3. Complete workflow (ingest + generate)")
    print("4. Update existing schema")
    
    choice = input("\nSelect example (1-4) or press Enter for all: ").strip()
    
    if choice == "1":
        ingest_schema_example()
    elif choice == "2":
        test_context_aware_after_ingestion()
    elif choice == "3":
        complete_workflow()
    elif choice == "4":
        update_schema_example()
    else:
        # Run all examples
        ingest_schema_example()
        test_context_aware_after_ingestion()
        complete_workflow()
        update_schema_example()
    
    print("\n" + "="*60)
    print("  Examples completed!")
    print("="*60 + "\n")
