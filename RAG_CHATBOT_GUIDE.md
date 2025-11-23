# RAG Chatbot Implementation Guide

## Overview

The chatbot uses **Retrieval-Augmented Generation (RAG)** with an **Agent Flow pipeline** built using `pyagentspec` and `wayflowcore`. This allows the chatbot to search through your documents and provide accurate, cited answers based on your personal document collection.

## Architecture

### Flow Pipeline

```
User Query → Search Documents → Generate Answer → Return Response with Citations
```

The agent flow consists of 3 main components:

1. **Search Node**: Uses Meilisearch hybrid search (keyword + semantic) to find relevant documents
2. **Answer Node**: Uses LLM (Qwen 2.5-72B) with retrieved context to generate an answer
3. **Citation System**: Tracks which documents were used and returns them as references

### Key Files

- **`backend/chat_agent.py`**: Main RAG agent flow implementation
- **`backend/prompt.py`**: System prompts for the chatbot (RAG_SYSTEM_PROMPT)
- **`backend/main.py`**: FastAPI endpoint `/api/v1/chat`
- **`hooks/useChat.ts`**: React hook for frontend integration
- **`components/chat/ChatWidget.tsx`**: Chat UI component

## How It Works

### 1. Document Ingestion & Indexing

When documents are uploaded:
- Text is extracted using multimodal LLM (for images/PDFs)
- Embeddings are generated using Together AI's `Alibaba-NLP/gte-modernbert-base`
- Documents are indexed in Meilisearch with both text content and embeddings
- Metadata is stored in SQLite

### 2. Agent Flow Execution

When a user asks a question:

```python
# Flow Definition
Start Node (user query)
    ↓
Search Node (search_documents tool)
    - Hybrid search with configurable semantic_ratio
    - Retrieves top-k relevant documents
    - Returns JSON with document content and metadata
    ↓
Answer Node (generate_answer tool)
    - Constructs prompt with user query + retrieved documents
    - LLM generates answer with citations
    - Extracts which documents were actually referenced
    ↓
End Node (returns response with citations)
```

### 3. Tool Implementations

#### `search_documents` Tool
```python
def search_documents(query: str, semantic_ratio: float = 0.5, limit: int = 5) -> str:
    """
    Search for relevant documents using Meilisearch hybrid search.
    
    Args:
        query: User's search query
        semantic_ratio: Balance between keyword (0.0) and semantic (1.0) search
        limit: Maximum number of documents to retrieve
        
    Returns:
        JSON string containing search results with document metadata and content
    """
```

#### `generate_answer` Tool
```python
def generate_answer(query: str, context_json: str) -> str:
    """
    Generate an answer using LLM with retrieved context.
    
    Args:
        query: User's original question
        context_json: JSON string containing retrieved documents
        
    Returns:
        JSON with generated answer and citations
    """
```

## Usage

### Backend API

```bash
POST /api/v1/chat
Content-Type: application/json

{
  "message": "What invoices do I have from Q4?",
  "semantic_ratio": 0.5,  // Optional: 0=keyword, 0.5=hybrid, 1=semantic
  "limit": 5              // Optional: max documents to retrieve
}
```

**Response:**
```json
{
  "answer": "Based on your documents, you have 2 invoices from Q4 2024...",
  "citations": [
    {
      "id": 123,
      "title": "invoice_q4_2024.pdf",
      "type": "invoice",
      "url": "http://localhost:8000/uploads/invoice_q4_2024.pdf",
      "summary": "Invoice for services rendered in Q4 2024"
    }
  ],
  "documentsFound": 2
}
```

### Frontend Usage

```tsx
import { useChat } from "@/hooks/useChat";

function MyComponent() {
  const chatMutation = useChat();
  
  const handleAsk = async (question: string) => {
    const response = await chatMutation.mutateAsync({
      message: question,
      semantic_ratio: 0.5,
      limit: 5
    });
    
    console.log(response.answer);
    console.log(response.citations);
  };
}
```

## Configuration

### Semantic Ratio

Controls the balance between keyword and semantic search:

- **0.0**: Pure keyword search (fast, exact matching)
- **0.5**: Hybrid search (balanced, recommended)
- **1.0**: Pure semantic search (slower, conceptual matching)

### LLM Model

The chatbot uses **Qwen 2.5-72B-Instruct** via Together AI:

```python
llm_config = OpenAiCompatibleConfig(
    name="Qwen/Qwen2.5-72B-Instruct",
    model_id="Qwen/Qwen2.5-72B-Instruct",
    url="https://api.together.xyz/v1/chat/completions/",
    default_generation_parameters=LlmGenerationConfig(
        temperature=0.7,
        top_p=0.95,
    )
)
```

### Embedding Model

Uses **Alibaba-NLP/gte-modernbert-base** (768 dimensions):

```python
client.embeddings.create(
    model="Alibaba-NLP/gte-modernbert-base",
    input=text
)
```

## RAG System Prompt

The chatbot is instructed to:
- Answer questions using ONLY information from retrieved documents
- Cite specific documents by ID and filename
- Synthesize information across multiple documents when relevant
- Admit when documents don't contain enough information
- Provide clear, well-structured responses with proper citations

See `backend/prompt.py` for the full RAG_SYSTEM_PROMPT.

## Example Queries

### Financial Questions
```
"How much did I spend on utilities in March 2024?"
"Show me all invoices from Acme Corp"
"What's the total amount due from my unpaid invoices?"
```

### Document Search
```
"Find my employment contract with TechCorp"
"Where is my auto insurance policy?"
"Show me my tax return from 2023"
```

### Information Extraction
```
"When does my lease agreement expire?"
"What medications did Dr. Jones prescribe?"
"What was discussed in the Q1 planning meeting?"
```

## Advantages of Agent Flow Approach

1. **Modular Design**: Each tool (search, answer) is independent and testable
2. **Transparent Execution**: Clear data flow between nodes
3. **Easy to Extend**: Add new tools (summarization, fact-checking, etc.)
4. **Error Handling**: Each node can handle errors gracefully
5. **Observable**: Can log and monitor each step of the flow

## Extending the Flow

You can easily add more nodes to the flow:

### Example: Add a Fact-Checking Node

```python
fact_check_tool = ServerTool(
    name="fact_check",
    description="Verify facts against multiple sources",
    inputs=[StringProperty(title="claim", description="Claim to verify")],
    outputs=[StringProperty(title="verification", description="Fact check result")]
)

fact_check_node = ToolNode(
    name="fact_check_node",
    tool=fact_check_tool
)

# Add to flow
flow = Flow(
    name="RAG Chat Flow with Fact Checking",
    nodes=[start_node, search_node, answer_node, fact_check_node, end_node],
    control_flow_connections=[
        ControlFlowEdge(name="start_to_search", from_node=start_node, to_node=search_node),
        ControlFlowEdge(name="search_to_answer", from_node=search_node, to_node=answer_node),
        ControlFlowEdge(name="answer_to_fact_check", from_node=answer_node, to_node=fact_check_node),
        ControlFlowEdge(name="fact_check_to_end", from_node=fact_check_node, to_node=end_node),
    ],
    # ... data flow connections
)
```

## Performance Considerations

- **Embedding Generation**: ~200ms per document (cached in Meilisearch)
- **Search**: ~50-100ms for hybrid search
- **LLM Generation**: 2-5s depending on context length
- **Total Latency**: ~3-6s per query

## Best Practices

1. **Document Preparation**: Extract and index text during upload for faster search
2. **Chunking**: For very large documents, consider splitting into smaller chunks
3. **Cache**: Store embeddings to avoid regeneration
4. **Limit Context**: Retrieve only top-k most relevant documents (default: 5)
5. **Monitor**: Log search queries and results for quality improvement

## Troubleshooting

### No Results Found
- Check if documents are properly indexed in Meilisearch
- Verify embeddings were generated during upload
- Try different semantic_ratio values

### Poor Answer Quality
- Increase `limit` to retrieve more documents
- Adjust `semantic_ratio` for better search results
- Verify document text extraction quality

### Slow Responses
- Reduce `limit` to fewer documents
- Use keyword search (semantic_ratio=0.0) for simple queries
- Consider response streaming for better UX

## Future Enhancements

- [ ] Add conversation history/memory
- [ ] Implement multi-turn conversations
- [ ] Add document re-ranking based on relevance
- [ ] Support for follow-up questions
- [ ] Query expansion for better retrieval
- [ ] Response streaming for faster perceived performance
- [ ] Multi-document summarization
- [ ] Fact verification across sources
