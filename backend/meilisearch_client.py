import meilisearch
from typing import Optional, Dict, List, Any

class MeilisearchClient:
    """Client for interacting with Meilisearch for document search."""
    
    def __init__(self, host: str = "http://localhost:7700", api_key: Optional[str] = None):
        """Initialize Meilisearch client."""
        self.client = meilisearch.Client(host, api_key)
        self.index_name = "documents"
        # Create index with explicit primary key if it doesn't exist
        self.index = self.client.index(self.index_name)
        try:
            self.client.create_index(self.index_name, {'primaryKey': 'id'})
        except Exception:
            # Index might already exist
            pass
        
    def setup_index(self, use_embeddings: bool = False):
        """
        Configure the documents index with searchable attributes and optional embedder.
        
        Args:
            use_embeddings: Whether to enable user-provided embeddings for semantic search
        """
        settings = {
            "searchableAttributes": ["filename", "content", "summary", "keywords"],
            "filterableAttributes": ["type", "parent_folder_id"],
            "sortableAttributes": ["upload_date"],
            "displayedAttributes": ["id", "filename", "type", "parent_folder_id"]
        }
        
        # Add embedder configuration for user-provided embeddings (Together AI)
        # Note: embeddings are optional - documents can be indexed with or without them
        if use_embeddings:
            settings["embedders"] = {
                "default": {
                    "source": "userProvided",
                    "dimensions": 768,  # Alibaba-NLP/gte-modernbert-base uses 768 dimensions
                    "binaryQuantized": False
                }
            }
        
        try:
            self.index.update_settings(settings)
            embedder_status = "with user-provided embeddings" if use_embeddings else "keyword-only"
            print(f"Meilisearch index '{self.index_name}' configured successfully ({embedder_status})")
        except Exception as e:
            print(f"Error configuring Meilisearch index: {e}")
            
    def index_document(self, doc_id: int, filename: str, content: str, 
                       doc_type: str, folder_id: Optional[int] = None,
                       embedding: Optional[list] = None, summary: Optional[str] = None,
                       keywords: Optional[list] = None):
        """
        Add or update a document in the Meilisearch index.
        
        Args:
            doc_id: Document ID from SQLite
            filename: Document filename
            content: Extracted text content
            doc_type: Document type (image, document, etc.)
            folder_id: Parent folder ID, if any
            embedding: Optional embedding vector for semantic search
            summary: Optional AI-generated summary
            keywords: Optional list of keywords
        """
        document = {
            "id": str(doc_id),
            "filename": filename,
            "content": content or "",
            "type": doc_type,
            "parent_folder_id": folder_id,
            "summary": summary or "",
            "keywords": " ".join(keywords) if keywords else ""  # Join keywords for text search
        }
        
        # Add embedding vector if provided
        if embedding:
            document["_vectors"] = {"default": embedding}
        
        try:
            self.index.add_documents([document])
            embed_status = "with embedding" if embedding else "without embedding"
            print(f"Indexed document {doc_id}: {filename} ({embed_status})")
        except Exception as e:
            print(f"Error indexing document {doc_id}: {e}")
            
    def search(self, query: str, semantic_ratio: float = 0.0, 
               filters: Optional[Dict] = None, limit: int = 20) -> Dict[str, Any]:
        """
        Search for documents using keyword or hybrid search.
        
        Args:
            query: Search query string
            semantic_ratio: 0=keyword only, 0.5=balanced, 1=semantic only (requires embedder)
            filters: Optional filters dict with keys 'type' and/or 'parent_folder_id'
            limit: Maximum number of results to return
            
        Returns:
            Search results with hits, totalHits, and processingTimeMs
        """
        opt_params = {
            "limit": limit
        }
        
        # Add hybrid search if semantic_ratio > 0 (requires embedder to be configured)
        if semantic_ratio > 0:
            opt_params["hybrid"] = {
                "semanticRatio": semantic_ratio,
                "embedder": "default"
            }
        
        # Build filter string
        if filters:
            filter_parts = []
            if "type" in filters:
                filter_parts.append(f"type = '{filters['type']}'")
            if "parent_folder_id" in filters:
                if filters["parent_folder_id"] is None:
                    filter_parts.append("parent_folder_id IS NULL")
                else:
                    filter_parts.append(f"parent_folder_id = {filters['parent_folder_id']}")
            if filter_parts:
                opt_params["filter"] = " AND ".join(filter_parts)
        
        try:
            results = self.index.search(query, opt_params)
            return results
        except Exception as e:
            print(f"Search error: {e}")
            return {"hits": [], " estimatedTotalHits": 0, "processingTimeMs": 0}
            
    def delete_document(self, doc_id: int):
        """
        Remove a document from the Meilisearch index.
        
        Args:
            doc_id: Document ID to delete
        """
        try:
            self.index.delete_document(str(doc_id))
            print(f"Deleted document {doc_id} from Meilisearch")
        except Exception as e:
            print(f"Error deleting document {doc_id} from Meilisearch: {e}")
            
    def delete_documents(self, doc_ids: List[int]):
        """
        Bulk delete documents from the Meilisearch index.
        
        Args:
            doc_ids: List of document IDs to delete
        """
        try:
            self.index.delete_documents([str(doc_id) for doc_id in doc_ids])
            print(f"Deleted {len(doc_ids)} documents from Meilisearch")
        except Exception as e:
            print(f"Error bulk deleting documents from Meilisearch: {e}")
