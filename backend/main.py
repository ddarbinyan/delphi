from fastapi import FastAPI, UploadFile, File, HTTPException, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List, Optional
import os
import json
import threading
from dotenv import load_dotenv
try:
    from .store import DocumentStore, VectorStore, FileStore
    from .meilisearch_client import MeilisearchClient
    from .extractor import process_document
    from .embeddings import generate_embedding
    from .chat_agent import chat as chat_agent
except ImportError as e:
    print(f"ImportError caught: {e}")
    from store import DocumentStore, VectorStore, FileStore
    from meilisearch_client import MeilisearchClient
    from extractor import process_document
    from embeddings import generate_embedding
    from chat_agent import chat as chat_agent

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

# Initialize Meilisearch with user-provided embeddings (Together AI)
meili_client = MeilisearchClient(host="http://localhost:7700")
load_dotenv("api.env")
try:
    meili_client.setup_index(use_embeddings=True)  # Enable Together AI embeddings
except Exception as e:
    print(f"Warning: Meilisearch setup failed: {e}")
    print("Continuing without search functionality...")

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory="backend/uploads"), name="uploads")

# Custom endpoint for serving files with proper headers for preview
@app.get("/api/v1/files/{filename}")
async def serve_file(filename: str):
    """Serve files with proper headers for browser preview."""
    file_path = os.path.join("backend/uploads", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine content type
    ext = os.path.splitext(filename)[1].lower()
    content_types = {
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }
    
    media_type = content_types.get(ext, 'application/octet-stream')
    
    return FileResponse(
        file_path,
        media_type=media_type,
        headers={
            "Content-Disposition": "inline",  # Display in browser instead of download
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "public, max-age=3600"
        }
    )

def process_document_pipeline(
    doc_id: int,
    file_path: str,
    filename: str,
    ext: str,
    doc_type: str,
    parent_folder_id: Optional[int],
    content: Optional[str],
    needs_extraction: bool
):
    """Background thread to process document after initial upload."""
    try:
        summary = ""
        keywords = []
        
        # Extract content using AI agent if needed
        reminder_data = {}
        if needs_extraction:
            try:
                # Determine if file is PDF or image
                is_pdf = ext.lower() == '.pdf'
                file_type = "PDF" if is_pdf else "image"
                
                print(f"[Background] Extracting text from {file_type}: {file_path}")
                result = process_document(file_path, filename, is_pdf=is_pdf)
                if result and result.get("text"):
                    content = result["text"]
                    summary = result.get("summary", "")
                    keywords = result.get("keywords", [])
                    reminder_data = result.get("reminder_data", {})
                    print(f"[Background] Extracted {len(content)} characters from {file_type}")
                    print(f"[Background] Summary: {summary}")
                    print(f"[Background] Keywords: {', '.join(keywords)}")
                    print(f"[Background] Reminder data: {reminder_data}")
                    
                    # Update document with extracted content
                    keywords_json = json.dumps(keywords) if keywords else None
                    doc_store.update_document_content(doc_id, content, summary, keywords_json)
            except Exception as e:
                print(f"[Background] AI Extraction error: {e}")
        
        # Create reminder for all actionable items
        print(f"[Reminders] Reminder data for {filename}: {reminder_data}")
        if reminder_data and reminder_data.get("requires_action"):
            print(f"[Reminders] Document {doc_id} requires action - creating reminder")
            try:
                from datetime import datetime, date
                due_date_str = reminder_data.get("due_date")
                action_title = reminder_data.get("action_title", f"Action required: {filename}")
                
                # Only create reminders if there's a due date (database requires NOT NULL)
                if not due_date_str:
                    print(f"[Reminders] Skipping reminder for document {doc_id} - no due date provided")
                else:
                    # Check if date is valid and if it's overdue
                    try:
                        due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
                        today = date.today()
                        
                        if due_date < today:
                            # Mark as overdue in the title
                            action_title = f"[OVERDUE] {action_title}"
                            print(f"[Reminders] Date {due_date_str} is in the past - marking as overdue")
                        
                        # Create reminder with valid due date
                        reminder_id = doc_store.add_reminder(
                            doc_id=doc_id,
                            title=action_title,
                            description=reminder_data.get("action_description", ""),
                            due_date=due_date_str,
                            category=reminder_data.get("category", "other")
                        )
                        print(f"[Reminders] Created reminder {reminder_id} for document {doc_id}")
                    except ValueError as e:
                        print(f"[Reminders] Invalid date format {due_date_str}: {e} - skipping reminder")
            except Exception as e:
                print(f"[Reminders] Error creating reminder for document {doc_id}: {e}")
        else:
            print(f"[Reminders] Document {doc_id} does not require action - skipping reminder")
        
        # Index in Meilisearch if content is available
        if content:
            try:
                # Generate embedding for semantic search
                embedding_text = f"{filename}: {content}"
                embedding = generate_embedding(embedding_text)
                
                if embedding is not None:
                    meili_client.index_document(
                        doc_id=doc_id,
                        filename=filename,
                        content=content,
                        doc_type=doc_type,
                        folder_id=parent_folder_id,
                        embedding=embedding,
                        summary=summary,
                        keywords=keywords
                    )
                    print(f"[Background] Indexed document {doc_id} in Meilisearch")
                    
                    # Mark as completed if we didn't need extraction (file with content)
                    if not needs_extraction:
                        cursor = doc_store.conn.cursor()
                        cursor.execute("UPDATE documents SET processing_status = 'completed' WHERE id = ?", (doc_id,))
                        doc_store.conn.commit()
                else:
                    print(f"[Background] Warning: Embedding generation failed for document {doc_id}")
            except Exception as e:
                print(f"[Background] Meilisearch indexing error: {e}")
        
        print(f"[Background] Document {doc_id} processing completed")
    except Exception as e:
        print(f"[Background] Error processing document {doc_id}: {e}")

@app.post("/api/v1/ingest")
async def upload_document(
    file: UploadFile = File(...), 
    folder_id: Optional[str] = Form(None),
    content: Optional[str] = Form(None)
):
    try:
        # Convert folder_id to int if provided
        parent_folder_id = int(folder_id) if folder_id and folder_id != "null" else None
        
        print(f"Upload - Received folder_id: {folder_id}, Converted to: {parent_folder_id}")
        if content:
            print(f"Upload - Received content: {len(content)} characters")
        
        # 1. Save file to disk immediately
        file_path = file_store.save_file(file)
        
        # 2. Determine type
        ext = os.path.splitext(file.filename)[1].lower()
        doc_type = "image" if ext in [".jpg", ".png", ".jpeg"] else "document"
        if "invoice" in file.filename.lower(): doc_type = "invoice"
        elif "receipt" in file.filename.lower(): doc_type = "receipt"
        
        # 3. Create document record immediately (without content for images)
        size = f"{file.size / 1024:.1f} KB" if file.size else "0 KB"
        
        doc_id = doc_store.add_document(
            filename=file.filename,
            path=file_path,
            type=doc_type,
            size=size,
            parent_folder_id=parent_folder_id,
            content=content or "",  # Empty for images, will be filled in background
            summary=None,
            keywords=None
        )
        
        print(f"Document created with ID: {doc_id}, parent_folder_id: {parent_folder_id}")
        
        # 4. Determine if we need AI extraction or just indexing
        needs_extraction = not content and ext in [".jpg", ".png", ".jpeg", ".webp", ".pdf"]
        
        # 5. Start background thread for processing (extraction, embedding, indexing)
        # Use daemon thread so it doesn't block server shutdown
        thread = threading.Thread(
            target=process_document_pipeline,
            args=(doc_id, file_path, file.filename, ext, doc_type, parent_folder_id, content, needs_extraction),
            daemon=True
        )
        thread.start()
        
        print(f"[Upload] Returning immediately, background processing started for doc {doc_id}")
        
        # 5. Return immediately - don't wait for background processing
        return {
            "id": doc_id, 
            "status": "success", 
            "filename": file.filename,
            "processing": "background"
        }
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
            "url": f"http://localhost:8000/api/v1/files/{os.path.basename(doc['path'])}",
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

class ChatRequest(BaseModel):
    message: str
    semantic_ratio: Optional[float] = 0.5
    limit: Optional[int] = 5

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

@app.get("/api/v1/reminders")
async def get_reminders():
    """Get all reminders."""
    try:
        reminders = doc_store.get_reminders()
        return [
            {
                "id": reminder["id"],
                "documentId": reminder["document_id"],
                "title": reminder["title"],
                "description": reminder["description"],
                "dueDate": reminder["due_date"],
                "category": reminder["category"],
                "status": reminder["status"],
                "createdAt": reminder["created_at"],
                "filename": reminder.get("filename"),
                "documentType": reminder.get("type")
            }
            for reminder in reminders
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/v1/reminders/{reminder_id}/complete")
async def complete_reminder(reminder_id: int):
    """Mark a reminder as completed."""
    try:
        doc_store.complete_reminder(reminder_id)
        return {"success": True, "message": "Reminder marked as completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Chat endpoint that uses RAG (Retrieval-Augmented Generation) to answer questions.
    
    The agent flow:
    1. Takes the user's question
    2. Searches relevant documents using Meilisearch (hybrid semantic + keyword search)
    3. Generates an answer using the LLM with retrieved context
    4. Returns the answer with citations to source documents
    """
    try:
        if not request.message or len(request.message.strip()) < 2:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        print(f"Chat request: {request.message}")
        
        # Execute the RAG flow using the chat agent
        result = chat_agent(
            user_query=request.message,
            semantic_ratio=request.semantic_ratio,
            limit=request.limit
        )
        
        # Enhance citations with URLs for the frontend
        enhanced_citations = []
        for citation in result.get("citations", []):
            doc_id = citation["id"]
            doc = doc_store.get_document(doc_id)
            if doc:
                enhanced_citations.append({
                    "id": doc["id"],
                    "title": citation["filename"],
                    "type": citation["type"],
                    "url": f"http://localhost:8000/uploads/{os.path.basename(doc['path'])}",
                    "summary": doc.get("summary", "")
                })
        
        return {
            "answer": result["answer"],
            "citations": enhanced_citations,
            "documentsFound": result["documents_found"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
