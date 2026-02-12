"""
Example: Updating database schema in Qdrant

This script demonstrates how to update an existing project's schema
when your database structure changes.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def update_schema_example():
    """Example: Update existing schema after database changes."""
    print("\n" + "="*60)
    print("  Schema Update Example")
    print("="*60)
    
    payload = {
        "project_id": "my-project-123",
        "db_type": "postgresql",
        "connection_string": "postgresql://user:password@localhost:5432/mydb"
    }
    
    print(f"\nUpdating schema for project: {payload['project_id']}")
    print("This will:")
    print("  1. Delete old schema")
    print("  2. Connect to database")
    print("  3. Extract fresh schema")
    print("  4. Store updated schema in Qdrant")
    
    response = requests.post(f"{BASE_URL}/update-schema", json=payload)
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        if result['success']:
            print(f"\nSchema Updated!")
            print(f"   Project ID: {result['project_id']}")
            print(f"   Tables Updated: {result['tables_ingested']}")
            print(f"   Message: {result['message']}")
        else:
            print(f"\nUpdate Failed!")
            print(f"   Error: {result.get('error')}")
            print(f"   Message: {result['message']}")
    else:
        print(f"\nHTTP Error: {response.text}")

def compare_ingest_vs_update():
    """Compare /ingest-schema vs /update-schema endpoints."""
    print("\n" + "="*60)
    print("  Ingest vs Update Comparison")
    print("="*60)
    
    print("\n/ingest-schema:")
    print("   - Can preserve existing schema (clear_existing=False)")
    print("   - Can replace schema (clear_existing=True)")
    print("   - More flexible")
    print("   - Use for initial setup or when you want control")
    
    print("\n/update-schema:")
    print("   - Always replaces existing schema")
    print("   - Simpler API (no clear_existing parameter)")
    print("   - More explicit intent")
    print("   - Use when schema has changed and needs refresh")
    
    print("\nRecommendation:")
    print("   - First time: Use /ingest-schema")
    print("   - Schema changed: Use /update-schema")

def workflow_with_update():
    """Complete workflow showing when to use update."""
    print("\n" + "="*60)
    print("  Complete Workflow: Initial Setup + Updates")
    print("="*60)
    
    project_id = "ecommerce-app"
    connection_string = "postgresql://user:pass@localhost:5432/ecommerce"
    
    # Step 1: Initial ingestion
    print("\nStep 1: Initial Schema Ingestion")
    print("   (First time setup)")
    
    ingest_payload = {
        "project_id": project_id,
        "db_type": "postgresql",
        "connection_string": connection_string,
        "clear_existing": False  # Don't need to clear on first run
    }
    
    response = requests.post(f"{BASE_URL}/ingest-schema", json=ingest_payload)
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            print(f"Ingested {result['tables_ingested']} tables")
    
    # Step 2: Use the schema
    print("\nStep 2: Using Context-Aware Generation")
    print("   (Normal operation)")
    
    gen_payload = {
        "question": "Get all orders from last week",
        "project_id": project_id,
        "db_type": "postgresql"
    }
    
    response = requests.post(f"{BASE_URL}/generate-sql", json=gen_payload)
    if response.status_code == 200:
        result = response.json()
        print(f"Generated SQL: {result.get('query', 'N/A')[:60]}...")
    
    # Step 3: Database schema changes
    print("\nStep 3: Database Schema Changed")
    print("   (Added new columns, tables, etc.)")
    print("   Simulating schema change...")
    
    # Step 4: Update schema
    print("\nStep 4: Update Schema in Qdrant")
    print("   (Refresh after changes)")
    
    update_payload = {
        "project_id": project_id,
        "db_type": "postgresql",
        "connection_string": connection_string
    }
    
    response = requests.post(f"{BASE_URL}/update-schema", json=update_payload)
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            print(f"Updated {result['tables_ingested']} tables")
            print(f"Message: {result['message']}")
    
    # Step 5: Continue using with fresh schema
    print("\nStep 5: Continue Using with Fresh Schema")
    print("   (AI now knows about new tables/columns)")
    
    gen_payload = {
        "question": "Show me data from the new table",
        "project_id": project_id,
        "db_type": "postgresql"
    }
    
    response = requests.post(f"{BASE_URL}/generate-sql", json=gen_payload)
    if response.status_code == 200:
        result = response.json()
        print(f"Decision: {result['decision']}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  SCHEMA UPDATE EXAMPLES")
    print("="*60)
    
    print("\nAvailable examples:")
    print("1. Basic schema update")
    print("2. Compare ingest vs update")
    print("3. Complete workflow (setup + update)")
    
    choice = input("\nSelect example (1-3) or press Enter for all: ").strip()
    
    if choice == "1":
        update_schema_example()
    elif choice == "2":
        compare_ingest_vs_update()
    elif choice == "3":
        workflow_with_update()
    else:
        # Run all examples
        update_schema_example()
        compare_ingest_vs_update()
        workflow_with_update()
    
    print("\n" + "="*60)
    print("  Examples completed!")
    print("="*60 + "\n")
