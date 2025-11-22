import os
import hashlib
from pathlib import Path
import meilisearch
import time

# Configuration
MEILISEARCH_URL = os.getenv("MEILISEARCH_URL", "http://localhost:7700")
MEILISEARCH_KEY = os.getenv("MEILISEARCH_MASTER_KEY", "masterKey")
INDEX_NAME = "personal_data"
RESOURCES_DIR = Path(__file__).parent.parent / "resources"

def get_client():
    return meilisearch.Client(MEILISEARCH_URL, MEILISEARCH_KEY)

def generate_id(file_path):
    """Generate a deterministic ID based on the file path."""
    return hashlib.md5(str(file_path).encode()).hexdigest()

def index_documents():
    client = get_client()
    
    # Create or get index
    index = client.index(INDEX_NAME)
    
    # Update filterable attributes for faceting
    index.update_filterable_attributes(["category"])
    
    documents = []
    
    if not RESOURCES_DIR.exists():
        print(f"Resources directory not found: {RESOURCES_DIR}")
        return

    print(f"Scanning documents in {RESOURCES_DIR}...")
    
    for file_path in RESOURCES_DIR.rglob("*"):
        if file_path.is_file() and file_path.suffix in ['.txt', '.md']:
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Determine category from parent folder name relative to resources dir
                relative_path = file_path.relative_to(RESOURCES_DIR)
                category = relative_path.parts[0] if len(relative_path.parts) > 1 else "uncategorized"
                
                doc = {
                    "id": generate_id(relative_path),
                    "title": file_path.name,
                    "content": content,
                    "category": category,
                    "path": str(relative_path)
                }
                documents.append(doc)
                print(f"Found: {relative_path}")
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

    if documents:
        task = index.add_documents(documents)
        print(f"Enqueued {len(documents)} documents for indexing. Task UID: {task.task_uid}")
        
        # Wait for task to complete (optional, for demo purposes)
        while True:
            status = client.get_task(task.task_uid)
            if status.status in ['succeeded', 'failed']:
                print(f"Indexing finished with status: {status.status}")
                break
            time.sleep(0.1)
    else:
        print("No documents found to index.")

def search(query, category=None):
    client = get_client()
    index = client.index(INDEX_NAME)
    
    search_params = {
        "limit": 5,
        "attributesToHighlight": ["content"]
    }
    
    if category:
        search_params["filter"] = f"category = '{category}'"
    
    print(f"\nSearching for '{query}'" + (f" in category '{category}'" if category else "") + "...")
    results = index.search(query, search_params)
    
    for hit in results['hits']:
        print("-" * 40)
        print(f"Title: {hit['title']}")
        print(f"Category: {hit['category']}")
        # Print highlighted content snippet if available, else full content truncated
        content_snippet = hit.get('_formatted', {}).get('content', hit['content'][:200])
        print(f"Content: {content_snippet}")
        print("-" * 40)

if __name__ == "__main__":
    try:
        # Check connection
        client = get_client()
        client.health()
        
        # Index documents
        index_documents()
        
        # Example searches
        search("bank account")
        search("hackathon", category="project_notes")
        search("passport")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure Meilisearch is running!")
        print("You can run it with Docker:")
        print(f"docker run -it --rm -p 7700:7700 -e MEILI_MASTER_KEY={MEILISEARCH_KEY} -v $(pwd)/meili_data:/meili_data getmeili/meilisearch:v1.13")
