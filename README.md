# Delphi - AI-Powered Drive

Delphi is a modern, intelligent file management system that combines the familiarity of a traditional cloud drive with powerful AI capabilities. It features instant search, folder management, and seamless document previews.

## 🚀 Features

- **Smart Storage**: Upload, organize, and manage files and folders.
- **Instant Search**: Powered by Meilisearch for lightning-fast keyword and semantic search.
- **Document Preview**: Built-in preview for PDFs and images without downloading.
- **Contextual Actions**: Move, delete, and manage files with ease.
- **Modern UI**: A clean, responsive interface built with Shadcn UI and Tailwind CSS.

## 🛠 Tech Stack

- **Frontend**: Next.js 14 (App Router), React, TypeScript, Tailwind CSS, Shadcn UI, TanStack Query.
- **Backend**: FastAPI (Python), SQLite.
- **Search Engine**: Meilisearch.
- **Infrastructure**: Docker (for Meilisearch).

## 📋 Prerequisites

Before you begin, ensure you have the following installed:
- **Node.js** (v18 or higher)
- **Python** (v3.8 or higher)
- **Docker** (for running the search engine)

## ⚡️ Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd delphi
```

### 2. Start Meilisearch (Search Engine)

Run Meilisearch using Docker. This is required for search functionality.

```bash
docker run -it --rm \
  -p 7700:7700 \
  -e MEILI_ENV='development' \
  -v $(pwd)/meili_data:/meili_data \
  getmeili/meilisearch:v1.13
```
*Keep this terminal window open.*

### 3. Setup & Run Backend

Open a new terminal window:

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload --port 8000
```
The backend will start at `http://localhost:8000`.

### 4. Environment Configuration (Optional)

To enable **Semantic Search** capabilities (Hybrid Search), you need to provide an OpenAI API key.

1. Create a `.env` file in the `backend/` directory.
2. Add your OpenAI API key:

```env
OPENAI_API_KEY=sk-your-api-key-here
```

If this key is present, the system will automatically configure Meilisearch to use OpenAI embeddings for semantic search.

### 5. Setup & Run Frontend

Open a third terminal window:

```bash
# Install dependencies
npm install

# Start the development server
npm run dev
```
The application will be available at `http://localhost:3000`.

## 🌱 Seeding Example Data

To populate the drive with realistic sample documents (Invoices, Receipts, Contracts, etc.) to test the search functionality:

1. Ensure the backend and Meilisearch are running.
2. Run the seed script:

```bash
cd backend
# Ensure venv is activated
python seed_database.py
```

This will create 10 sample documents with rich content that you can search for immediately.

## 🔍 Search Configuration

The search system uses **Meilisearch**.
- **Endpoint**: `http://localhost:7700`
- **Index Name**: `documents`
- **Searchable Attributes**: `filename`, `content`
- **Filterable Attributes**: `type`, `parent_folder_id`

To enable **Semantic Search** (Hybrid Search), you can configure an OpenAI API key in the backend `meilisearch_client.py` or environment variables (future feature). Currently, it defaults to keyword search which is highly effective for the seeded content.

## 📂 Project Structure

```
.
├── app/                    # Next.js App Router pages
├── backend/                # FastAPI Backend
│   ├── main.py             # API Endpoints
│   ├── store.py            # Database & File System Logic
│   ├── meilisearch_client.py # Search Engine Client
│   ├── seed_database.py    # Data Seeding Script
│   ├── metadata.db         # SQLite Database
│   └── uploads/            # File Storage
├── components/             # React Components
│   ├── drive/              # File Grid, List, Folder components
│   ├── preview/            # Document Preview Modal
│   ├── search/             # Search Bar & Results
│   └── ui/                 # Shadcn UI primitives
├── hooks/                  # Custom React Hooks (useDocuments, useSearch, etc.)
└── public/                 # Static assets
```
