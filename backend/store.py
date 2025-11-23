import sqlite3
import chromadb
import os
import shutil
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import UploadFile

# --- Configuration ---
# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
SQLITE_DB_PATH = os.path.join(BASE_DIR, "metadata.db")
CHROMA_DB_PATH = os.path.join(BASE_DIR, "chroma_db")

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)

class DocumentStore:
    """Manages metadata in SQLite."""
    def __init__(self):
        self.conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        cursor = self.conn.cursor()
        
        # Create folders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS folders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                parent_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES folders(id) ON DELETE CASCADE
            )
        """)
        
        # Create documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                path TEXT NOT NULL,
                type TEXT NOT NULL,
                size TEXT NOT NULL,
                upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                summary TEXT,
                sender TEXT,
                parent_folder_id INTEGER,
                content TEXT,
                keywords TEXT,
                FOREIGN KEY (parent_folder_id) REFERENCES folders(id) ON DELETE CASCADE
            )
        """)
        
        # Add keywords column if it doesn't exist (for existing databases)
        try:
            cursor.execute("ALTER TABLE documents ADD COLUMN keywords TEXT")
            self.conn.commit()
        except sqlite3.OperationalError:
            # Column already exists
            pass
        self.conn.commit()

    def create_folder(self, name: str, parent_id: Optional[int] = None) -> int:
        """Create a new folder."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO folders (name, parent_id) VALUES (?, ?)",
            (name, parent_id)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_folders(self, parent_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all folders at a specific level (None = root)."""
        cursor = self.conn.cursor()
        if parent_id is None:
            cursor.execute("SELECT * FROM folders WHERE parent_id IS NULL ORDER BY name")
        else:
            cursor.execute("SELECT * FROM folders WHERE parent_id = ? ORDER BY name", (parent_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_folder(self, folder_id: int) -> Optional[Dict[str, Any]]:
        """Get a single folder by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM folders WHERE id = ?", (folder_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def delete_folder(self, folder_id: int) -> bool:
        """Delete a folder and all its contents (files and subfolders) recursively."""
        cursor = self.conn.cursor()
        
        # First, get all documents in this folder
        cursor.execute("SELECT id, path FROM documents WHERE parent_folder_id = ?", (folder_id,))
        documents = cursor.fetchall()
        
        # Get all subfolders
        cursor.execute("SELECT id FROM folders WHERE parent_id = ?", (folder_id,))
        subfolders = cursor.fetchall()
        
        # Recursively delete subfolders
        for subfolder in subfolders:
            self.delete_folder(subfolder["id"])
        
        # Delete all documents in this folder
        for doc in documents:
            doc_id = doc["id"]
            file_path = doc["path"]
            
            # Delete from filesystem
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Deleted file: {file_path}")
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")
            
            # Delete from SQLite
            cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            
            # Delete from ChromaDB (vector store)
            # Note: This requires access to VectorStore, which we'll handle in the API endpoint
        
        # Finally, delete the folder itself
        cursor.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
        self.conn.commit()
        
        return cursor.rowcount > 0

    def add_document(self, filename: str, path: str, type: str, size: str, parent_folder_id: Optional[int] = None, content: Optional[str] = None, summary: Optional[str] = None, keywords: Optional[str] = None) -> int:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO documents (filename, path, type, size, parent_folder_id, content, summary, keywords) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (filename, path, type, size, parent_folder_id, content, summary, keywords)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_documents(self, parent_folder_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get documents, optionally filtered by parent folder. None = root level."""
        cursor = self.conn.cursor()
        if parent_folder_id is None:
            cursor.execute("SELECT * FROM documents WHERE parent_folder_id IS NULL ORDER BY upload_date DESC")
        else:
            cursor.execute("SELECT * FROM documents WHERE parent_folder_id = ? ORDER BY upload_date DESC", (parent_folder_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def move_document(self, doc_id: int, target_folder_id: Optional[int]) -> bool:
        """Move a document to a different folder."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE documents SET parent_folder_id = ? WHERE id = ?",
            (target_folder_id, doc_id)
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def get_document(self, doc_id: int) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def delete_document(self, doc_id: int) -> bool:
        """Delete a document from SQLite by ID."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        self.conn.commit()
        return cursor.rowcount > 0

class VectorStore:
    """Manages embeddings in ChromaDB."""
    def __init__(self):
        self.client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        self.collection = self.client.get_or_create_collection(name="documents")

    def add_document(self, doc_id: str, text: str, metadata: Dict[str, Any]):
        self.collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[doc_id]
        )

    def search(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from ChromaDB by ID."""
        try:
            self.collection.delete(ids=[doc_id])
            return True
        except Exception:
            return False

class FileStore:
    """Manages raw files on disk."""
    def save_file(self, file: UploadFile) -> str:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return file_path

    def get_file_path(self, filename: str) -> str:
        return os.path.join(UPLOAD_DIR, filename)

    def delete_file(self, file_path: str) -> bool:
        """Delete a file from the filesystem."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False
