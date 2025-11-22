import argparse
import os
import hashlib
from pathlib import Path
import meilisearch
import time

def get_client(url, key):
    return meilisearch.Client(url, key)

def generate_id(file_path):
    """Generate a deterministic ID based on the file path."""
    return hashlib.md5(str(file_path).encode()).hexdigest()

def index_documents(client, resources_dir, index_name):
    # Create or get index
    index = client.index(index_name)
    
    # Update filterable attributes for faceting
    index.update_filterable_attributes(["category"])
    
    documents = []
    
    if not resources_dir.exists():
        print(f"Resources directory not found: {resources_dir}")
        return

    print(f"Scanning documents in {resources_dir}...")
    
    for file_path in resources_dir.rglob("*"):
        if file_path.is_file() and file_path.suffix in ['.txt', '.md']:
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Determine category from parent folder name relative to resources dir
                relative_path = file_path.relative_to(resources_dir)
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

def search(client, query, index_name, category=None):
    index = client.index(index_name)
    
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

def main():
    parser = argparse.ArgumentParser(description="Meilisearch Engine CLI")
    parser.add_argument("--url", default=os.getenv("MEILISEARCH_URL", "http://localhost:7700"), help="Meilisearch URL")
    parser.add_argument("--key", default=os.getenv("MEILISEARCH_MASTER_KEY", "masterKey"), help="Meilisearch Master Key")
    parser.add_argument("--index-name", default="personal_data", help="Index name")
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Index command
    index_parser = subparsers.add_parser("index", help="Index documents from a directory")
    index_parser.add_argument("--resources-dir", required=True, help="Path to resources directory")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search for documents")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--category", help="Filter by category")
    
    args = parser.parse_args()
    
    try:
        client = get_client(args.url, args.key)
        client.health()
        
        if args.command == "index":
            index_documents(client, Path(args.resources_dir), args.index_name)
        elif args.command == "search":
            search(client, args.query, args.index_name, args.category)
            
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure Meilisearch is running!")

if __name__ == "__main__":
    main()
