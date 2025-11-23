from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
import os
try:
    from .store import DocumentStore, VectorStore, FileStore
    from .meilisearch_client import MeilisearchClient
except ImportError:
    from store import DocumentStore, VectorStore, FileStore
    from meilisearch_client import MeilisearchClient

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://128.179.201.181:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize stores
doc_store = DocumentStore()
vector_store = VectorStore()
file_store = FileStore()

# Initialize Meilisearch (keyword-only for now, no embedder)
meili_client = MeilisearchClient(host="http://localhost:7700")
openai_key = os.getenv("OPENAI_API_KEY")  # Optional: for semantic search
try:
    meili_client.setup_index(openai_api_key=openai_key)
except Exception as e:
    print(f"Warning: Meilisearch setup failed: {e}")
    print("Continuing without search functionality...")

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory="backend/uploads"), name="uploads")

@app.post("/api/v1/ingest")
async def upload_document(
    file: UploadFile = File(...), 
    folder_id: Optional[str] = Form(None),
    content: Optional[str] = Form(None)  # NEW: Extracted text from multimodal LLM agent
):
    try:
        # Convert folder_id to int if provided
        parent_folder_id = int(folder_id) if folder_id and folder_id != "null" else None
        
        print(f"Upload - Received folder_id: {folder_id}, Converted to: {parent_folder_id}")
        if content:
            print(f"Upload - Received content: {len(content)} characters")
        
        # 1. Save file to disk
        file_path = file_store.save_file(file)
        
        # 2. Determine type (simple logic for now)
        ext = os.path.splitext(file.filename)[1].lower()
        doc_type = "image" if ext in [".jpg", ".png", ".jpeg"] else "document"
        if "invoice" in file.filename.lower(): doc_type = "invoice"
        elif "receipt" in file.filename.lower(): doc_type = "receipt"
        
        # 3. Save metadata + content to SQLite
        size = f"{file.size / 1024:.1f} KB" if file.size else "0 KB"
        
        doc_id = doc_store.add_document(
            filename=file.filename,
            path=file_path,
            type=doc_type,
            size=size,
            parent_folder_id=parent_folder_id,
            content=content or ""  # Store extracted text
        )
        
        print(f"Document created with ID: {doc_id}, parent_folder_id: {parent_folder_id}")
        
        # 4. Index in Meilisearch if content provided
        if content:
            try:
                meili_client.index_document(
                    doc_id=doc_id,
                    filename=file.filename,
                    content=content,
                    doc_type=doc_type,
                    folder_id=parent_folder_id
                )
            except Exception as e:
                print(f"Meilisearch indexing error: {e}")
        
        return {"id": doc_id, "status": "success", "filename": file.filename}
    except Exception as e:
        print(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/documents")
async def get_documents(folder_id: Optional[int] = None):
    docs = doc_store.get_documents(parent_folder_id=folder_id)
    # Transform for frontend
    return [
        {
            "id": str(doc["id"]),
            "title": doc["filename"],
            "type": doc["type"],
            "sender": doc["sender"] or "Unknown",
            "summary": doc["summary"] or "No summary available",
            "url": f"http://localhost:8000/uploads/{os.path.basename(doc['path'])}",
            "createdAt": doc["upload_date"],
            "size": doc["size"],
            "parentFolderId": doc.get("parent_folder_id")
        }
        for doc in docs
    ]

@app.get("/api/v1/search")
async def search_documents(
    q: str,
    semantic_ratio: float = 0.0,  # 0=keyword, 0.5=hybrid, 1=semantic (requires OpenAI)
    folder_id: Optional[int] = None,
    type: Optional[str] = None,
    limit: int = 20
):
    """
    Search documents using Meilisearch hybrid search.
    
    Query params:
        q: Search query (required)
        semantic_ratio: 0=keyword only, 0.5=balanced, 1=semantic (default: 0)
        folder_id: Filter by folder
        type: Filter by document type
        limit: Max results (default: 20)
    """
    try:
        if not q or len(q) < 2:
            return {"hits": [], "totalHits": 0, "query": q}
        
        # Build filters
        filters = {}
        if folder_id is not None:
            filters["parent_folder_id"] = folder_id
        if type:
            filters["type"] = type
        
        # Search via Meilisearch
        results = meili_client.search(
            query=q,
            semantic_ratio=semantic_ratio,
            filters=filters if filters else None,
            limit=limit
        )
        
        # Enhance results with full metadata from SQLite
        enhanced_hits = []
        for hit in results.get("hits", []):
            doc_id = int(hit["id"])
            doc = doc_store.get_document(doc_id)
            if doc:
                enhanced_hits.append({
                    "id": doc["id"],
                    "title": doc["filename"],
                    "url": f"/uploads/{os.path.basename(doc['path'])}",
                    "type": doc["type"],
                    "size": doc["size"],
                    "sender": doc["sender"] or "Unknown",
                    "summary": doc["summary"] or "No summary available",
                    "uploadDate": doc["upload_date"],
                    "parentFolderId": doc.get("parent_folder_id"),
                    "content": doc.get("content", ""),
                    "_score":hit.get("_rankingScore", 0),
                    "_semanticScore": hit.get("_semanticScore", 0)
                })
        
        return {
            "hits": enhanced_hits,
            "totalHits": results.get("estimatedTotalHits", len(enhanced_hits)),
            "processingTimeMs": results.get("processingTimeMs", 0),
            "query": q,
            "semanticRatio": semantic_ratio
        }
    except Exception as e:
        print(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/documents/{doc_id}")
async def delete_document(doc_id: int):
    try:
        # 1. Get document metadata to find file path
        doc = doc_store.get_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # 2. Delete from file system
        file_deleted = file_store.delete_file(doc["path"])
        
        # 3. Delete from SQLite
        db_deleted = doc_store.delete_document(doc_id)
        
        # 4. Delete from ChromaDB (if exists)
        try:
            vector_store.delete_document(str(doc_id))
        except Exception:
            pass  # Ignore if not in vector store
        
        # 5. Delete from Meilisearch
        try:
            meili_client.delete_document(doc_id)
        except Exception as e:
            print(f"Meilisearch delete error: {e}")
        
        if file_deleted and db_deleted:
            return {"status": "success", "message": f"Document {doc_id} deleted"}
        else:
            return {
                "status": "partial", 
                "message": "Document partially deleted",
                "file_deleted": file_deleted,
                "db_deleted": db_deleted
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Folder Management Endpoints
from pydantic import BaseModel

class CreateFolderRequest(BaseModel):
    name: str
    parent_id: Optional[int] = None

@app.post("/api/v1/folders")
async def create_folder(request: CreateFolderRequest):
    try:
        folder_id = doc_store.create_folder(name=request.name, parent_id=request.parent_id)
        return {"id": folder_id, "status": "success", "name": request.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/folders")
async def get_folders(parent_id: Optional[int] = None):
    folders = doc_store.get_folders(parent_id=parent_id)
    return [
        {
            "id": str(folder["id"]),
            "name": folder["name"],
            "parentId": folder.get("parent_id"),
            "createdAt": folder["created_at"],
            "type": "folder"
        }
        for folder in folders
    ]

@app.get("/api/v1/folders/{folder_id}/contents")
async def get_folder_contents(folder_id: int):
    """Get both folders and documents in a specific folder."""
    folders = doc_store.get_folders(parent_id=folder_id)
    documents = doc_store.get_documents(parent_folder_id=folder_id)
    
    folder_items = [
        {
            "id": f"folder-{folder['id']}",
            "name": folder["name"],
            "parentId": folder.get("parent_id"),
            "createdAt": folder["created_at"],
            "type": "folder",
            "isFolder": True
        }
        for folder in folders
    ]
    
    doc_items = [
        {
            "id": str(doc["id"]),
            "title": doc["filename"],
            "type": doc["type"],
            "sender": doc["sender"] or "Unknown",
            "summary": doc["summary"] or "No summary available",
            "url": f"http://localhost:8000/uploads/{doc['filename']}",
            "createdAt": doc["upload_date"],
            "size": doc["size"],
            "parentFolderId": doc.get("parent_folder_id"),
            "isFolder": False
        }
        for doc in documents
    ]
    
    return {"folders": folder_items, "documents": doc_items}

@app.delete("/api/v1/folders/{folder_id}")
async def delete_folder(folder_id: int):
    try:
        # Get all documents in the folder (and subfolders) before deleting
        def get_all_document_ids(fid: int) -> list:
            """Recursively get all document IDs in a folder and its subfolders."""
            doc_ids = []
            
            # Get documents in this folder
            docs = doc_store.get_documents(parent_folder_id=fid)
            doc_ids.extend([doc["id"] for doc in docs])
            
            # Get subfolders
            cursor = doc_store.conn.cursor()
            cursor.execute("SELECT id FROM folders WHERE parent_id = ?", (fid,))
            subfolders = cursor.fetchall()
            
            # Recursively get documents from subfolders
            for subfolder in subfolders:
                doc_ids.extend(get_all_document_ids(subfolder["id"]))
            
            return doc_ids
        
        # Get all document IDs before deletion
        all_doc_ids = get_all_document_ids(folder_id)
        
        # Delete from vector store
        for doc_id in all_doc_ids:
            try:
                vector_store.delete_document(str(doc_id))
            except Exception as e:
                print(f"Error deleting document {doc_id} from vector store: {e}")
        
        # Delete from Meilisearch
        if all_doc_ids:
            try:
                meili_client.delete_documents(all_doc_ids)
            except Exception as e:
                print(f"Error deleting documents from Meilisearch: {e}")
        
        # Delete folder and all contents (handles filesystem and SQLite)
        success = doc_store.delete_folder(folder_id)
        
        if success:
            print(f"Deleted folder {folder_id} with {len(all_doc_ids)} documents")
            return {
                "status": "success", 
                "message": f"Folder {folder_id} and {len(all_doc_ids)} documents deleted"
            }
        else:
            raise HTTPException(status_code=404, detail="Folder not found")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting folder: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

class MoveDocumentRequest(BaseModel):
    target_folder_id: Optional[int] = None

@app.patch("/api/v1/documents/{doc_id}/move")
async def move_document(doc_id: int, request: MoveDocumentRequest):
    try:
        success = doc_store.move_document(doc_id, request.target_folder_id)
        if success:
            return {"status": "success", "message": f"Document {doc_id} moved"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
