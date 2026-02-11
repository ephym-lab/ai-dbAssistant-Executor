#!/usr/bin/env python3
"""
Script to reset the Qdrant collection for database schemas.

This script will:
1. Delete the existing 'database_schemas' collection if it exists
2. Recreate it with the proper configuration for text-based embeddings

Run this script before using the /ingest-schema endpoint if you encounter
collection configuration errors.
"""

import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

# Load environment variables
load_dotenv()

def reset_collection():
    """Reset the database_schemas collection in Qdrant."""
    
    # Get Qdrant configuration
    url = os.getenv("QDRANT_URL", "http://localhost:6333")
    api_key = os.getenv("QDRANT_API_KEY")
    collection_name = os.getenv("QDRANT_COLLECTION_NAME", "database_schemas")
    
    # Initialize client
    if api_key:
        client = QdrantClient(url=url, api_key=api_key)
    else:
        client = QdrantClient(url=url)
    
    try:
        # Check if collection exists
        collections = client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        if collection_name in collection_names:
            print(f"Deleting existing collection: {collection_name}")
            client.delete_collection(collection_name=collection_name)
            print(f"✓ Collection '{collection_name}' deleted successfully")
        else:
            print(f"Collection '{collection_name}' does not exist")
        
        # Create new collection with vector config for FastEmbed
        print(f"\nCreating new collection: {collection_name}")
        print("Configuration: 384-dimensional vectors (BAAI/bge-small-en-v1.5), Cosine distance")
        
        from qdrant_client.models import Distance, VectorParams
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=384,  # BAAI/bge-small-en-v1.5 embedding size
                distance=Distance.COSINE
            )
        )
        print(f"✓ Collection '{collection_name}' created successfully")
        print("\nYou can now use the /ingest-schema endpoint!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Qdrant Collection Reset Script")
    print("=" * 60)
    print()
    
    success = reset_collection()
    
    if success:
        print("\n" + "=" * 60)
        print("Reset completed successfully!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("Reset failed. Please check the error above.")
        print("=" * 60)
        exit(1)
