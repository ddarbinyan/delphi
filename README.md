# Delphi - AI-Powered Drive

Delphi is a modern, intelligent file management system that combines the familiarity of a traditional cloud drive with powerful AI capabilities. It features instant search, folder management, seamless document previews, and intelligent reminder extraction.

## 🚀 Features

- **Smart Storage**: Upload, organize, and manage files and folders.
- **AI Chat Assistant**: Interactive RAG-powered chatbot to query your documents and get instant answers.
- **Intelligent Reminders**: Automatically extracts actionable items, deadlines, and due dates from uploaded documents (bills, appointments, contracts, etc.).
- **Overdue Tracking**: Automatically detects and marks overdue reminders with clear indicators.
- **Hybrid Search**: Powered by Meilisearch with Together AI embeddings for lightning-fast semantic and keyword search.
- **Document Analysis**: AI-powered extraction of summaries, keywords, and actionable items from PDFs and images.
- **Document Preview**: Built-in preview for PDFs and images without downloading, with keyboard navigation.
- **Contextual Actions**: Move, delete, and manage files with ease.
- **Modern UI**: A clean, responsive interface built with Shadcn UI and Tailwind CSS.

## 🛠 Tech Stack

- **Frontend**: Next.js 14 (App Router), React, TypeScript, Tailwind CSS, Shadcn UI, TanStack Query, Framer Motion.
- **Backend**: FastAPI (Python), SQLite, pyagentspec, wayflowcore.
- **AI/LLM**: Together AI (Qwen/Qwen2.5-VL-72B-Instruct for vision, openai/gpt-oss-120b for text analysis).
- **Vector Database**: ChromaDB for document embeddings.
- **Search Engine**: Meilisearch with Together AI embeddings for hybrid search.
- **PDF Processing**: PyMuPDF for text extraction from PDFs.
- **Infrastructure**: Local Meilisearch and ChromaDB instances.

## 📋 Prerequisites

Before you begin, ensure you have the following installed:
- **Node.js** (v18 or higher)
- **Python** (v3.8 or higher)
- **Meilisearch** (v1.13 or higher)

## ⚡️ Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd delphi
```

### 2. Start Meilisearch (Search Engine)

Run Meilisearch locally. This is required for search functionality.

```bash
# Run Meilisearch (assuming it's installed via Homebrew or available in PATH)
meilisearch --env development --db-path ./meili_data
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
cd .. && uvicorn backend.main:app --reload --port 8000
```
The backend will start at `http://localhost:8000`.

### 4. Environment Configuration (Required for AI Features)

To enable **AI features** (chat, document analysis, reminders, semantic search), you need to provide a Together AI API key.

1. Create a `api.env` file in the `backend/` directory.
2. Add your Together AI API key:

```env
TOGETHER_API_KEY=your-together-api-key-here
```

This key enables:
- **AI Chat Assistant**: RAG-powered chatbot for querying documents
- **Document Analysis**: Automatic extraction of summaries and keywords
- **Reminder Extraction**: Intelligent detection of actionable items and deadlines
- **Semantic Search**: Hybrid search with Together AI embeddings via Meilisearch

Get your API key at [together.ai](https://together.ai)

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

The search system uses **Meilisearch** with **Together AI embeddings** for hybrid semantic + keyword search.
- **Endpoint**: `http://localhost:7700`
- **Index Name**: `documents`
- **Searchable Attributes**: `filename`, `content`, `summary`, `keywords`
- **Filterable Attributes**: `type`, `parent_folder_id`
- **Embeddings**: Together AI vectors stored in Meilisearch for semantic similarity

The system automatically enables hybrid search when a `TOGETHER_API_KEY` is provided in `api.env`.

## 🤖 AI Features

### Chat Assistant
- **RAG-Powered**: Queries your document collection using vector similarity
- **Context-Aware**: Provides answers with citations to source documents
- **Real-time**: Interactive chat widget with document preview integration

### Reminder System
- **Automatic Extraction**: Analyzes uploaded documents for actionable items
- **Smart Detection**: Identifies bills, appointments, renewals, deadlines
- **Categories**: Automatically categorizes reminders (payment, appointment, subscription, etc.)
- **Overdue Tracking**: Marks past-due reminders with `[OVERDUE]` prefix
- **Due Date Parsing**: Extracts and tracks due dates from document content

### Document Analysis
- **Dual Processing**: Separate workflows for images (OCR with vision model) and PDFs (text extraction)
- **Summary Generation**: AI-generated summaries for quick document understanding
- **Keyword Extraction**: Automatic tagging for improved searchability
- **Vision Model**: Qwen/Qwen2.5-VL-72B-Instruct for image-based documents
- **Text Model**: openai/gpt-oss-120b for PDF analysis and chat

## 🔄 Agent Workflows

Delphi uses **pyagentspec** and **wayflowcore** to orchestrate intelligent document processing through two specialized agent workflows. Each workflow is a directed graph of nodes that process documents sequentially.

### Image Processing Workflow

**Flow**: `Start → Vision Extraction → Summarization → Reminder Analysis → End`

1. **Start Node**
   - Inputs: `image_path`, `filename`
   - Initializes the workflow with the path to an image document

2. **Vision Extraction Node** (`analyze_image`)
   - **Tool**: Vision LLM (Qwen/Qwen2.5-VL-72B-Instruct)
   - **Purpose**: Performs OCR on images to extract text content
   - **Process**: 
     - Loads image bytes and determines format (JPEG, PNG, etc.)
     - Creates a prompt with system instructions and the image
     - Calls the vision model via Together AI API
     - Returns extracted text or empty string if no text found
   - **Output**: `extracted_text`

3. **Summarization Node** (`summarize_and_extract_keywords`)
   - **Tool**: Text LLM (openai/gpt-oss-120b)
   - **Purpose**: Generates document summary and extracts searchable keywords
   - **Process**:
     - Takes extracted text (skips if less than 10 characters)
     - Sends to text model with summarization prompt
     - Parses JSON response containing summary and keyword list
     - Handles markdown code blocks in LLM responses
   - **Output**: `analysis_result` (JSON with `summary` and `keywords`)

4. **Reminder Analysis Node** (`analyze_for_reminder`)
   - **Tool**: Text LLM (openai/gpt-oss-120b)
   - **Purpose**: Detects actionable items and deadlines
   - **Process**:
     - Combines extracted text, summary, and keywords into context
     - Sends to text model with strict reminder analysis prompt
     - Identifies if document requires action (bills, appointments, renewals, deadlines)
     - Extracts due dates, categories, action titles, and descriptions
     - Returns structured JSON with reminder metadata
   - **Output**: `reminder_data` (JSON with `requires_action`, `category`, `due_date`, `action_title`, `action_description`)

5. **End Node**
   - Aggregates all outputs: `text`, `analysis`, `reminder`
   - Returns complete document processing results

**Data Flow**:
- `image_path` → Vision Extraction
- `extracted_text` → Summarization + Reminder Analysis
- `filename` → Reminder Analysis (for context)
- `analysis_result` → Reminder Analysis (provides keywords/summary context)
- All outputs → End Node

### PDF Processing Workflow

**Flow**: `Start → Text Extraction → Summarization → Reminder Analysis → End`

1. **Start Node**
   - Inputs: `pdf_path`, `filename`
   - Initializes the workflow with the path to a PDF document

2. **PDF Text Extraction Node** (`extract_pdf_text`)
   - **Tool**: PyMuPDF (fitz library)
   - **Purpose**: Extracts raw text from PDF files without requiring vision model
   - **Process**:
     - Opens PDF using PyMuPDF
     - Iterates through all pages
     - Extracts text from each page using `.get_text()`
     - Concatenates all page text
     - Validates minimum text length (10 characters)
   - **Output**: `extracted_text`
   - **Note**: Much faster than vision model since it reads native PDF text

3. **Summarization Node** (`summarize_and_extract_keywords`)
   - **Identical to image workflow**
   - Processes extracted PDF text to generate summary and keywords

4. **Reminder Analysis Node** (`analyze_for_reminder`)
   - **Identical to image workflow**
   - Analyzes PDF content for actionable items and deadlines

5. **End Node**
   - Aggregates all outputs: `text`, `analysis`, `reminder`
   - Returns complete document processing results

**Data Flow**:
- `pdf_path` → PDF Text Extraction
- `extracted_text` → Summarization + Reminder Analysis
- `filename` → Reminder Analysis (for context)
- `analysis_result` → Reminder Analysis (provides keywords/summary context)
- All outputs → End Node

### Key Differences Between Workflows

| Aspect | Image Workflow | PDF Workflow |
|--------|---------------|--------------|
| **Extraction Method** | Vision LLM (Qwen) via API | PyMuPDF text extraction |
| **Speed** | Slower (API call + model inference) | Faster (native text reading) |
| **Accuracy** | Good for scanned docs, photos | Perfect for digital PDFs |
| **Cost** | API credits per image | Local, no API cost |
| **Use Case** | Screenshots, scanned docs, photos | Native PDFs with selectable text |

### Workflow Orchestration

Both workflows use:
- **Control Flow Edges**: Define sequential execution order between nodes
- **Data Flow Edges**: Pass outputs from one node as inputs to another
- **Tool Registry**: Maps tool names to Python function implementations
- **AgentSpecLoader**: Loads and executes the flow with registered tools
- **Conversation Context**: Maintains state throughout the workflow execution

The workflows automatically handle errors, parse JSON responses, and provide fallback values if any step fails.

## 📂 Project Structure

```
.
├── app/                    # Next.js App Router pages
│   ├── page.tsx            # Main drive page with document browsing
│   ├── reminders/          # Reminders page with overdue tracking
│   └── layout.tsx          # Root layout with sidebar and chat widget
├── backend/                # FastAPI Backend
│   ├── main.py             # API Endpoints & Document Processing Pipeline
│   ├── store.py            # Database & File System Logic
│   ├── meilisearch_client.py # Search Engine Client with Together AI
│   ├── embeddings.py       # Vector embedding generation
│   ├── extractor.py        # Document text extraction & AI analysis
│   ├── chat_agent.py       # RAG-powered chat agent
│   ├── prompt.py           # LLM prompts for analysis & reminders
│   ├── seed_database.py    # Data Seeding Script
│   ├── metadata.db         # SQLite Database (documents, folders, reminders)
│   ├── uploads/            # File Storage
│   └── chroma_db/          # ChromaDB vector storage
├── components/             # React Components
│   ├── chat/               # Chat widget with RAG integration
│   ├── drive/              # File Grid, List, Folder components
│   ├── preview/            # Document Preview Modal with keyboard nav
│   ├── search/             # Search Bar & Results
│   ├── layout/             # Sidebar & Header
│   └── ui/                 # Shadcn UI primitives
├── hooks/                  # Custom React Hooks
│   ├── useChat.ts          # Chat assistant integration
│   ├── useDocuments.ts     # Document CRUD operations
│   ├── useSearch.ts        # Search functionality
│   └── useUpload.ts        # File upload with progress
├── contexts/               # React Context providers
├── meili_data/             # Meilisearch data directory
└── public/                 # Static assets
```
