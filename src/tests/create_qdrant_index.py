"""
Create payload index for project_id field in Qdrant.

This script creates an index on the project_id field to enable
efficient filtering when retrieving schemas.
"""

import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import PayloadSchemaType

# Load environment variables
load_dotenv()

def create_project_id_index():
    """Create index on project_id field."""
    
    # Get Qdrant configuration
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    collection_name = os.getenv("QDRANT_COLLECTION_NAME", "database_schemas")
    
    print("="*60)
    print("Creating Qdrant Payload Index")
    print("="*60)
    print(f"\nQdrant URL: {qdrant_url}")
    print(f"Collection: {collection_name}")
    print(f"Field: project_id")
    
    try:
        # Initialize Qdrant client
        client = QdrantClient(
            url=qdrant_url,
            api_key=qdrant_api_key
        )
        
        # Create payload index
        print("\nCreating index...")
        client.create_payload_index(
            collection_name=collection_name,
            field_name="project_id",
            field_schema=PayloadSchemaType.KEYWORD
        )
        
        print("Index created successfully!")
        print("\nThe project_id field is now indexed for efficient filtering.")
        
    except Exception as e:
        if "already exists" in str(e).lower():
            print("Index already exists - no action needed")
        else:
            print(f"Error: {e}")
            raise

if __name__ == "__main__":
    create_project_id_index()
