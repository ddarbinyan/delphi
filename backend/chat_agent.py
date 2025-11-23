"""
Chat Agent Flow with RAG (Retrieval-Augmented Generation)

This module implements a conversational agent that:
1. Takes a user query
2. Searches relevant documents using Meilisearch
3. Generates a response with citations using LLM
"""

import warnings
warnings.filterwarnings('ignore')

from pyagentspec.llms import OpenAiCompatibleConfig, LlmGenerationConfig
import os
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional
import json

# Load environment
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, "api.env")
load_dotenv(env_path)

# LLM Configuration
llm_config = OpenAiCompatibleConfig(
    name="openai/gpt-oss-120b",
    model_id="openai/gpt-oss-120b",
    url="https://api.together.xyz/v1/chat/completions/",
    default_generation_parameters=LlmGenerationConfig(
        temperature=0.7,
        top_p=0.95,
    )
)

from wayflowcore.agentspec import AgentSpecLoader
from wayflowcore.messagelist import Message, TextContent
from wayflowcore.models import Prompt
from pyagentspec.flows.flow import Flow
from pyagentspec.flows.nodes import StartNode, EndNode, ToolNode
from pyagentspec.flows.edges import ControlFlowEdge, DataFlowEdge
from pyagentspec.tools import ServerTool
from pyagentspec.property import StringProperty, ListProperty

try:
    from .meilisearch_client import MeilisearchClient
    from .embeddings import generate_embedding
    from .store import DocumentStore
    from .prompt import RAG_SYSTEM_PROMPT
except ImportError:
    from meilisearch_client import MeilisearchClient
    from embeddings import generate_embedding
    from store import DocumentStore
    from prompt import RAG_SYSTEM_PROMPT

# Initialize clients
meili_client = MeilisearchClient(host="http://localhost:7700")
doc_store = DocumentStore()

# Query classification prompt
QUERY_CLASSIFIER_PROMPT = """You are a query classifier for a document management system. Your task is to determine if a user's query requires searching through their personal documents or if it can be answered with a general conversational response.

Classify queries as:
- "SEARCH" if the query is asking about specific documents, information in files, or anything that would require looking at the user's personal documents
- "CHAT" if the query is a greeting, small talk, general question, or doesn't require document access

Examples of SEARCH queries:
- "What invoices do I have from March?"
- "Find my employment contract"
- "How much did I spend on utilities?"
- "Show me documents about the project"
- "What's in my tax return?"

Examples of CHAT queries:
- "Hi", "Hello", "Hey"
- "How are you?"
- "What can you do?"
- "Thanks", "Thank you"
- "Good morning"

Respond with ONLY one word: either "SEARCH" or "CHAT"."""

# Query refinement prompt
QUERY_REFINEMENT_PROMPT = """You are a search query optimizer for a document management system. Your task is to generate comprehensive keywords that will help find relevant documents, even if those keywords don't appear in the original question.

Critical Instructions:
1. Think about what DOCUMENTS might contain the answer, not just words in the question
2. Include document types that would have this information (tickets, receipts, invoices, itineraries, passports, visas, boarding passes, confirmations, statements, bills, contracts, etc.)
3. Add related concepts and evidence types that would prove or show the information
4. Include location names, countries, cities, states, landmarks, airports, addresses
5. Add temporal indicators (dates, months, years, seasons)
6. Think about synonyms, alternative phrasings, and related terms
7. Consider what metadata or context clues might appear in relevant documents
8. Generate 10-20 diverse keywords that cast a wide net

Key Principle: If someone asks "Which countries have I been to?", they won't have a document saying "countries visited". Instead, look for: travel tickets, flight bookings, hotel reservations, visa stamps, passport stamps, itineraries, boarding passes, foreign receipts, international transactions, customs forms, etc.

Examples:

User: "Which countries have I been to?"
Keywords: travel ticket flight boarding pass passport visa hotel booking itinerary reservation international trip abroad vacation tourism destination airport immigration customs stamp foreign country nation state city

User: "What invoices do I have from Acme Corp in March 2024?"
Keywords: Acme Corp invoice March 2024 bill payment receipt statement charge purchase order PO transaction

User: "Find my employment contract with TechCorp"
Keywords: employment contract TechCorp agreement job offer work salary compensation benefits hire position role employee

User: "When did I travel to USA?"
Keywords: USA America United States travel ticket flight hotel itinerary booking trip visa passport international airport immigration customs boarding pass reservation confirmation San Diego Los Angeles New York California Texas Florida

User: "How much did I spend on utilities last month?"
Keywords: utilities bill payment expense electricity water gas internet phone service telecom energy invoice statement charge account

User: "Show me the tax documents from last year"
Keywords: tax return 2023 2024 IRS income W-2 1099 deduction refund filing federal state revenue

User: "Do I have any medical records?"
Keywords: medical health doctor prescription medication pharmacy treatment diagnosis hospital clinic patient visit appointment insurance claim

User: "When did I buy my car?"
Keywords: car vehicle auto purchase sale contract registration title loan financing dealer invoice receipt DMV

Respond with ONLY the keywords/phrases, separated by spaces. No explanations or formatting."""


def classify_query(query: str) -> str:
    """
    Classify whether a query needs document search or can be answered conversationally.
    
    Args:
        query: User's query
        
    Returns:
        JSON string with classification: {"needs_search": "yes" or "no", "original_query": query}
    """
    try:
        print(f"Classifying query: {query}")
        
        # Create prompt
        prompt = Prompt(messages=[
            Message(
                role="system",
                contents=[TextContent(content=QUERY_CLASSIFIER_PROMPT)]
            ),
            Message(
                role="user",
                contents=[TextContent(content=query)]
            )
        ])
        
        # Generate classification
        llm_component = AgentSpecLoader().load_component(llm_config)
        completion = llm_component.generate(prompt)
        classification = completion.message.content.strip().upper()
        
        needs_search = "yes" if "SEARCH" in classification else "no"
        print(f"Classification: {classification} -> needs_search: {needs_search}")
        
        return json.dumps({"needs_search": needs_search, "original_query": query})
        
    except Exception as e:
        print(f"Error classifying query: {e}")
        # Default to searching if there's an error
        return json.dumps({"needs_search": "yes", "original_query": query})


def refine_query(original_query: str) -> str:
    """
    Refine user query into optimal search keywords.
    
    Args:
        original_query: User's original question
        
    Returns:
        JSON string with refined keywords and original query
    """
    try:
        print(f"Refining query: {original_query}")
        
        # Create prompt
        prompt = Prompt(messages=[
            Message(
                role="system",
                contents=[TextContent(content=QUERY_REFINEMENT_PROMPT)]
            ),
            Message(
                role="user",
                contents=[TextContent(content=original_query)]
            )
        ])
        
        # Generate refined query
        llm_component = AgentSpecLoader().load_component(llm_config)
        completion = llm_component.generate(prompt)
        keywords = completion.message.content.strip()
        
        print(f"Refined keywords: {keywords}")
        
        return json.dumps({
            "search_query": keywords,
            "original_query": original_query
        })
        
    except Exception as e:
        print(f"Error refining query: {e}")
        # Fall back to original query
        return json.dumps({
            "search_query": original_query,
            "original_query": original_query
        })


def generate_conversational_response(query: str) -> str:
    """
    Generate a friendly conversational response without document search.
    
    Args:
        query: User's query
        
    Returns:
        JSON string with answer and empty citations
    """
    try:
        print(f"Generating conversational response for: {query}")
        
        prompt = Prompt(messages=[
            Message(
                role="system",
                contents=[TextContent(content="""You are Delphi, a helpful AI assistant for a document management system. 
Respond in a friendly, conversational manner. Keep responses concise and helpful.
If the user asks what you can do, explain that you can help them find and understand information in their documents.
If it's a greeting, respond warmly and ask how you can help with their documents.""")]
            ),
            Message(
                role="user",
                contents=[TextContent(content=query)]
            )
        ])
        
        llm_component = AgentSpecLoader().load_component(llm_config)
        completion = llm_component.generate(prompt)
        answer = completion.message.content.strip()
        
        print(f"Generated conversational response")
        
        return json.dumps({
            "answer": answer,
            "citations": []
        })
        
    except Exception as e:
        print(f"Error generating conversational response: {e}")
        return json.dumps({
            "answer": "Hello! I'm Delphi, your document assistant. How can I help you with your documents today?",
            "citations": []
        })


def search_documents(query: str, semantic_ratio: str = "0.5", limit: str = "20") -> str:
    """
    Search for relevant documents using Meilisearch hybrid search.
    Searches each keyword individually and combines results for better recall.
    
    Args:
        query: User's search query (can be JSON string with search_query field or plain string)
        semantic_ratio: Balance between keyword (0.0) and semantic (1.0) search (as string)
        limit: Maximum number of documents to retrieve (as string)
        
    Returns:
        JSON string containing search results with document metadata and content
    """
    try:
        # Convert string parameters to appropriate types
        semantic_ratio_float = float(semantic_ratio)
        max_limit = int(limit)
        
        # Extract search query from JSON if needed
        search_query = query
        try:
            query_data = json.loads(query)
            search_query = query_data.get("search_query", query)
        except (json.JSONDecodeError, TypeError):
            # If not JSON, use as-is
            pass
        
        print(f"Searching documents for query: {search_query}")
        
        # Split keywords and search each one individually
        keywords = search_query.split()
        print(f"Searching {len(keywords)} keywords individually: {keywords[:5]}...")
        
        # Track all found documents with their best scores
        doc_scores = {}  # doc_id -> {"doc": doc_data, "score": best_score, "matched_keywords": []}
        
        # Search each keyword individually
        for keyword in keywords:
            try:
                results = meili_client.search(
                    query=keyword,
                    semantic_ratio=semantic_ratio_float,
                    limit=max_limit
                )
                
                # Process hits from this keyword search
                for hit in results.get("hits", []):
                    doc_id = int(hit["id"])
                    score = hit.get("_rankingScore", 0)
                    
                    # If we haven't seen this document yet, or if this score is better
                    if doc_id not in doc_scores:
                        doc = doc_store.get_document(doc_id)
                        if doc and doc.get("content"):
                            doc_scores[doc_id] = {
                                "doc": {
                                    "id": doc["id"],
                                    "filename": doc["filename"],
                                    "type": doc["type"],
                                    "content": doc["content"][:1500],
                                    "summary": doc.get("summary", ""),
                                },
                                "score": score,
                                "matched_keywords": [keyword]
                            }
                    else:
                        # Update score if this keyword match is stronger
                        doc_scores[doc_id]["score"] = max(doc_scores[doc_id]["score"], score)
                        doc_scores[doc_id]["matched_keywords"].append(keyword)
                        
            except Exception as keyword_error:
                print(f"Error searching keyword '{keyword}': {keyword_error}")
                continue
        
        # Sort documents by score (descending) and number of matched keywords
        sorted_docs = sorted(
            doc_scores.values(),
            key=lambda x: (x["score"], len(x["matched_keywords"])),
            reverse=True
        )
        
        # Prepare final results with scores
        enhanced_results = []
        for item in sorted_docs[:max_limit]:
            doc_data = item["doc"]
            doc_data["score"] = item["score"]
            doc_data["matched_keywords_count"] = len(item["matched_keywords"])
            enhanced_results.append(doc_data)
        
        print(f"Found {len(enhanced_results)} unique documents from {len(keywords)} keywords")
        return json.dumps({"results": enhanced_results, "total": len(enhanced_results)})
        
    except Exception as e:
        print(f"Error searching documents: {e}")
        return json.dumps({"results": [], "total": 0, "error": str(e)})


def calculate(expression: str) -> str:
    """
    Safely evaluate a mathematical expression.
    
    Args:
        expression: Mathematical expression to evaluate (e.g., "22.49 + 2.49 + 108.80 + 9.60")
        
    Returns:
        JSON string with the calculation result
    """
    try:
        # Clean the expression - remove currency symbols and extra spaces
        cleaned = expression.replace('€', '').replace('CHF', '').replace('$', '').replace('USD', '').strip()
        
        # Only allow numbers, basic operators, parentheses, and spaces
        import re
        if not re.match(r'^[\d\s\+\-\*\/\.\(\)]+$', cleaned):
            return json.dumps({
                "result": None,
                "error": "Invalid expression. Only numbers and basic operators (+, -, *, /, parentheses) are allowed."
            })
        
        # Evaluate safely
        result = eval(cleaned)
        
        print(f"Calculation: {expression} = {result}")
        
        return json.dumps({
            "result": round(result, 2),
            "expression": expression,
            "error": None
        })
        
    except Exception as e:
        print(f"Calculation error: {e}")
        return json.dumps({
            "result": None,
            "error": f"Failed to calculate: {str(e)}"
        })


def analyze_calculation_needs(query: str, context_json: str) -> str:
    """
    Analyze if the query requires calculations and extract the numbers from documents.
    
    Args:
        query: User's original question
        context_json: JSON string containing retrieved documents
        
    Returns:
        JSON string with calculation analysis
    """
    try:
        # Parse context
        context_data = json.loads(context_json)
        documents = context_data.get("results", [])
        
        if not documents:
            return json.dumps({
                "needs_calculation": False,
                "calculations": [],
                "query": query,
                "context_json": context_json
            })
        
        # Sort documents by relevance score
        documents = sorted(documents, key=lambda x: x.get('score', 0), reverse=True)
        top_documents = documents[:8]
        
        # Build context string
        context_text = "\n\n".join([
            f"Document {i+1} (ID: {doc['id']}, Filename: {doc['filename']}):\n{doc['content']}"
            for i, doc in enumerate(top_documents)
        ])
        
        # Prompt to analyze calculation needs
        analysis_prompt = """You are a calculation analysis expert. Analyze if the user's query requires mathematical calculations.

Your task:
1. Determine if the query asks for sums, totals, averages, differences, or other calculations
2. Extract all relevant numbers from the documents with their context (what they represent)
3. Identify what calculations need to be performed
4. Group numbers by currency or unit if applicable

Respond with a JSON object:
{
  "needs_calculation": true/false,
  "calculation_type": "sum" or "average" or "difference" or "product" or "none",
  "number_groups": [
    {
      "currency": "EUR" or "CHF" or "USD" or "none",
      "numbers": [{"value": 22.49, "source": "bus ticket from Document 1"}, ...],
      "operation": "sum" or "average" etc.
    }
  ]
}

Return ONLY valid JSON, no explanations."""
        
        prompt = Prompt(messages=[
            Message(
                role="system",
                contents=[TextContent(content=analysis_prompt)]
            ),
            Message(
                role="user",
                contents=[TextContent(content=f"""Query: {query}

Documents:
{context_text}

Analyze if calculations are needed and extract the numbers.""")]
            )
        ])
        
        llm_component = AgentSpecLoader().load_component(llm_config)
        completion = llm_component.generate(prompt)
        analysis = completion.message.content.strip()
        
        # Parse the analysis
        import re
        json_match = re.search(r'\{[^}]+\}', analysis, re.DOTALL)
        if json_match:
            analysis_data = json.loads(json_match.group())
        else:
            analysis_data = json.loads(analysis)
        
        print(f"Calculation analysis: needs={analysis_data.get('needs_calculation', False)}")
        
        return json.dumps({
            "needs_calculation": analysis_data.get("needs_calculation", False),
            "calculation_data": analysis_data,
            "query": query,
            "context_json": context_json
        })
        
    except Exception as e:
        print(f"Error analyzing calculations: {e}")
        # If analysis fails, assume no calculation needed
        return json.dumps({
            "needs_calculation": False,
            "calculations": [],
            "query": query,
            "context_json": context_json
        })


def perform_calculations(analysis_json: str) -> str:
    """
    Perform the calculations identified by the analysis agent.
    
    Args:
        analysis_json: JSON string from analyze_calculation_needs
        
    Returns:
        JSON string with calculation results
    """
    try:
        analysis_data = json.loads(analysis_json)
        
        if not analysis_data.get("needs_calculation", False):
            return json.dumps({
                "calculation_results": [],
                "query": analysis_data.get("query", ""),
                "context_json": analysis_data.get("context_json", "{}")
            })
        
        calc_data = analysis_data.get("calculation_data", {})
        number_groups = calc_data.get("number_groups", [])
        
        results = []
        for group in number_groups:
            currency = group.get("currency", "none")
            numbers = group.get("numbers", [])
            operation = group.get("operation", "sum")
            
            # Extract numeric values
            values = [n["value"] for n in numbers if isinstance(n, dict) and "value" in n]
            
            if not values:
                continue
            
            # Perform calculation
            if operation == "sum":
                result = sum(values)
            elif operation == "average":
                result = sum(values) / len(values)
            elif operation == "product":
                result = 1
                for v in values:
                    result *= v
            else:
                result = sum(values)  # Default to sum
            
            results.append({
                "currency": currency,
                "operation": operation,
                "values": values,
                "result": round(result, 2),
                "sources": [n.get("source", "") for n in numbers if isinstance(n, dict)]
            })
        
        print(f"Performed {len(results)} calculations")
        
        return json.dumps({
            "calculation_results": results,
            "query": analysis_data.get("query", ""),
            "context_json": analysis_data.get("context_json", "{}")
        })
        
    except Exception as e:
        print(f"Error performing calculations: {e}")
        return json.dumps({
            "calculation_results": [],
            "query": analysis_data.get("query", ""),
            "context_json": analysis_data.get("context_json", "{}")
        })


def generate_answer(calculation_json: str) -> str:
    """
    Generate an answer using LLM with retrieved context and calculation results.
    
    Args:
        calculation_json: JSON string from perform_calculations containing query, context, and calculation results
        
    Returns:
        Generated answer with citations
    """
    try:
        # Parse calculation data
        calc_data = json.loads(calculation_json)
        query = calc_data.get("query", "")
        context_json = calc_data.get("context_json", "{}")
        calculation_results = calc_data.get("calculation_results", [])
        
        # Parse context
        context_data = json.loads(context_json)
        documents = context_data.get("results", [])
        
        if not documents:
            return json.dumps({
                "answer": "I couldn't find any relevant documents to answer your question. Please try rephrasing your query or upload more documents.",
                "citations": []
            })
        
        # Sort documents by relevance score (higher is better)
        documents = sorted(documents, key=lambda x: x.get('score', 0), reverse=True)
        
        # Take top documents but keep enough for context (up to 8 documents)
        top_documents = documents[:8]
        
        # Build context string for LLM
        context_text = "\n\n".join([
            f"Document {i+1} (ID: {doc['id']}, Filename: {doc['filename']}, Relevance: {doc.get('score', 0):.2f}):\n{doc['content']}"
            for i, doc in enumerate(top_documents)
        ])
        
        # Add calculation results to context if available
        calc_context = ""
        if calculation_results:
            calc_context = "\n\nCalculation Results:\n"
            for i, calc in enumerate(calculation_results, 1):
                currency_str = f" {calc['currency']}" if calc['currency'] != 'none' else ""
                calc_context += f"\nCalculation {i}:\n"
                calc_context += f"  Operation: {calc['operation']}\n"
                calc_context += f"  Values: {calc['values']}\n"
                calc_context += f"  Result: {calc['result']}{currency_str}\n"
                calc_context += f"  Sources: {', '.join(calc['sources'][:3])}\n"
        
        # Create prompt with structured citation instructions
        citation_prompt = RAG_SYSTEM_PROMPT + """

CRITICAL CITATION FORMAT:
When citing information from documents, use this EXACT format: [CITE:doc_id]
Examples:
- "The bus ticket cost 22.49 € [CITE:29]"
- "You spent 108.80 CHF on sports food [CITE:30]"
- "The train ticket was 9.60 CHF [CITE:31]"

Rules:
1. Place [CITE:doc_id] immediately after the information from that document
2. Use the actual document ID number (e.g., 29, 30, 31)
3. You can cite multiple documents: "Information from doc A [CITE:1] and doc B [CITE:2]"
4. Only cite documents you actually use in your answer
5. If calculation results are provided, use them directly - do NOT perform mental arithmetic
6. DO NOT mention document IDs, filenames, or "Document X" in your answer text - only use [CITE:X] tags
7. Write naturally as if speaking to the user - citations are added automatically via [CITE:X] tags

WRONG: "According to Document 1 (ID: 29, Screenshot_2023.png), the ticket was 22.49 €"
RIGHT: "The bus ticket was 22.49 € [CITE:29]"

This citation format allows us to properly track which documents you reference."""
        
        prompt = Prompt(messages=[
            Message(
                role="system",
                contents=[TextContent(content=citation_prompt)]
            ),
            Message(
                role="user",
                contents=[TextContent(content=f"""Question: {query}

Retrieved Documents:
{context_text}{calc_context}

Please answer the question based on the provided documents and calculation results (if any). Remember to use [CITE:doc_id] format when referencing information.""")]
            )
        ])
        
        # Generate response
        llm_component = AgentSpecLoader().load_component(llm_config)
        completion = llm_component.generate(prompt)
        answer = completion.message.content.strip()
        
        # Extract citations using the [CITE:doc_id] format
        import re
        
        # Find all [CITE:doc_id] tags
        cite_pattern = r'\[CITE:(\d+)\]'
        cited_doc_ids = set(re.findall(cite_pattern, answer))
        
        # Build citations list from cited document IDs (deduplicated)
        citations = []
        doc_id_map = {str(doc['id']): doc for doc in documents}
        seen_doc_ids = set()
        
        for doc_id_str in sorted(cited_doc_ids, key=int):
            if doc_id_str in doc_id_map and doc_id_str not in seen_doc_ids:
                doc = doc_id_map[doc_id_str]
                citations.append({
                    "id": doc['id'],
                    "filename": doc['filename'],
                    "type": doc['type']
                })
                seen_doc_ids.add(doc_id_str)
        
        # Remove [CITE:X] tags from the answer for cleaner display
        # Replace them with superscript numbers for visual reference
        citation_mapping = {doc_id: idx + 1 for idx, doc_id in enumerate(sorted(cited_doc_ids, key=int))}
        
        def replace_cite_tag(match):
            doc_id = match.group(1)
            if doc_id in citation_mapping:
                return f" [{citation_mapping[doc_id]}]"
            return ""
        
        answer_clean = re.sub(cite_pattern, replace_cite_tag, answer)
        
        print(f"Generated answer with {len(citations)} citations from {len(documents)} retrieved documents")
        
        return json.dumps({
            "answer": answer_clean,
            "citations": citations
        })
        
    except Exception as e:
        print(f"Error generating answer: {e}")
        return json.dumps({
            "answer": f"I encountered an error while generating the answer: {str(e)}",
            "citations": []
        })


# Define tools
classify_tool = ServerTool(
    name="classify_query",
    description="Classify if a query needs document search or conversational response.",
    inputs=[StringProperty(title="query", description="User's query")],
    outputs=[StringProperty(title="classification", description="JSON with needs_search and original_query")]
)

refine_tool = ServerTool(
    name="refine_query",
    description="Refine user query into search keywords.",
    inputs=[StringProperty(title="original_query", description="User's original question")],
    outputs=[StringProperty(title="refined", description="JSON with search_query and original_query")]
)

conversational_tool = ServerTool(
    name="generate_conversational_response",
    description="Generate a conversational response without document search.",
    inputs=[StringProperty(title="query", description="User's query")],
    outputs=[StringProperty(title="response", description="JSON string with answer and citations")]
)

search_tool = ServerTool(
    name="search_documents",
    description="Search for relevant documents using hybrid semantic and keyword search.",
    inputs=[
        StringProperty(title="query", description="User's search query (keywords)"),
        StringProperty(title="semantic_ratio", description="Balance between keyword and semantic search (default: 0.5)"),
        StringProperty(title="limit", description="Maximum documents to retrieve (default: 5)")
    ],
    outputs=[StringProperty(title="search_results", description="JSON string with search results")]
)

calculation_analysis_tool = ServerTool(
    name="analyze_calculation_needs",
    description="Analyze if the query requires calculations and extract numbers from documents.",
    inputs=[
        StringProperty(title="query", description="User's original question"),
        StringProperty(title="context_json", description="JSON string containing retrieved documents")
    ],
    outputs=[StringProperty(title="analysis", description="JSON string with calculation analysis")]
)

calculation_tool = ServerTool(
    name="perform_calculations",
    description="Perform mathematical calculations on extracted numbers.",
    inputs=[
        StringProperty(title="analysis_json", description="JSON string from calculation analysis")
    ],
    outputs=[StringProperty(title="calculation_results", description="JSON string with calculation results")]
)

answer_tool = ServerTool(
    name="generate_answer",
    description="Generate an answer based on retrieved documents and calculation results.",
    inputs=[
        StringProperty(title="calculation_json", description="JSON string containing query, context, and calculation results")
    ],
    outputs=[StringProperty(title="response", description="JSON string with answer and citations")]
)

# Define the Search Flow (with query refinement)
search_start_node = StartNode(
    name="search_start",
    inputs=[
        StringProperty(title="user_query", description="User's original question"),
        StringProperty(title="semantic_ratio", description="Balance between keyword and semantic search"),
        StringProperty(title="limit", description="Maximum documents to retrieve")
    ]
)

refine_node = ToolNode(
    name="refine_node",
    tool=refine_tool
)

search_node = ToolNode(
    name="search_node",
    tool=search_tool
)

calc_analysis_node = ToolNode(
    name="calc_analysis_node",
    tool=calculation_analysis_tool
)

calc_perform_node = ToolNode(
    name="calc_perform_node",
    tool=calculation_tool
)

answer_node = ToolNode(
    name="answer_node",
    tool=answer_tool
)

search_end_node = EndNode(
    name="search_end",
    outputs=[StringProperty(title="response", description="Final response with answer and citations")]
)

search_flow = Flow(
    name="RAG Search Flow with Calculations",
    start_node=search_start_node,
    nodes=[search_start_node, refine_node, search_node, calc_analysis_node, calc_perform_node, answer_node, search_end_node],
    control_flow_connections=[
        ControlFlowEdge(name="start_to_refine", from_node=search_start_node, to_node=refine_node),
        ControlFlowEdge(name="refine_to_search", from_node=refine_node, to_node=search_node),
        ControlFlowEdge(name="search_to_calc_analysis", from_node=search_node, to_node=calc_analysis_node),
        ControlFlowEdge(name="calc_analysis_to_calc_perform", from_node=calc_analysis_node, to_node=calc_perform_node),
        ControlFlowEdge(name="calc_perform_to_answer", from_node=calc_perform_node, to_node=answer_node),
        ControlFlowEdge(name="answer_to_end", from_node=answer_node, to_node=search_end_node),
    ],
    data_flow_connections=[
        # Original query flows to refine node
        DataFlowEdge(
            name="query_to_refine",
            source_node=search_start_node,
            source_output="user_query",
            destination_node=refine_node,
            destination_input="original_query"
        ),
        # Refined search query flows to search node
        DataFlowEdge(
            name="refined_to_search",
            source_node=refine_node,
            source_output="refined",
            destination_node=search_node,
            destination_input="query"
        ),
        # Search parameters flow from start to search
        DataFlowEdge(
            name="semantic_ratio_to_search",
            source_node=search_start_node,
            source_output="semantic_ratio",
            destination_node=search_node,
            destination_input="semantic_ratio"
        ),
        DataFlowEdge(
            name="limit_to_search",
            source_node=search_start_node,
            source_output="limit",
            destination_node=search_node,
            destination_input="limit"
        ),
        # Original query flows to calculation analysis
        DataFlowEdge(
            name="query_to_calc_analysis",
            source_node=search_start_node,
            source_output="user_query",
            destination_node=calc_analysis_node,
            destination_input="query"
        ),
        # Search results flow to calculation analysis
        DataFlowEdge(
            name="search_to_calc_analysis",
            source_node=search_node,
            source_output="search_results",
            destination_node=calc_analysis_node,
            destination_input="context_json"
        ),
        # Analysis results flow to calculation performer
        DataFlowEdge(
            name="analysis_to_calc_perform",
            source_node=calc_analysis_node,
            source_output="analysis",
            destination_node=calc_perform_node,
            destination_input="analysis_json"
        ),
        # Calculation results flow to answer node
        DataFlowEdge(
            name="calc_results_to_answer",
            source_node=calc_perform_node,
            source_output="calculation_results",
            destination_node=answer_node,
            destination_input="calculation_json"
        ),
        # Answer flows to end
        DataFlowEdge(
            name="answer_to_end",
            source_node=answer_node,
            source_output="response",
            destination_node=search_end_node,
            destination_input="response"
        )
    ]
)

# Register tool implementations
tool_registry = {
    "classify_query": classify_query,
    "refine_query": refine_query,
    "generate_conversational_response": generate_conversational_response,
    "search_documents": search_documents,
    "analyze_calculation_needs": analyze_calculation_needs,
    "perform_calculations": perform_calculations,
    "generate_answer": generate_answer
}


def chat(user_query: str, semantic_ratio: float = 0.7, limit: int = 10) -> Dict[str, Any]:
    """
    Main chat function that processes user queries using the RAG flow.
    
    Args:
        user_query: User's question
        semantic_ratio: Balance between keyword and semantic search (0.0 to 1.0, default 0.7 for better concept matching)
        limit: Maximum number of documents to retrieve (default 10 for comprehensive answers)
        
    Returns:
        dict with 'answer', 'citations', and 'documents_found'
    """
    try:
        # Step 1: Classify the query
        classification_result = classify_query(user_query)
        classification_data = json.loads(classification_result)
        needs_search = classification_data.get("needs_search", "yes")
        
        print(f"Query classification: needs_search={needs_search}")
        
        # Step 2: Handle based on classification
        if needs_search == "no":
            # Generate conversational response without document search
            response_json = generate_conversational_response(user_query)
            response_data = json.loads(response_json)
            
            return {
                "answer": response_data.get("answer", ""),
                "citations": [],
                "documents_found": 0
            }
        else:
            # Execute the search flow with query refinement
            executable_flow = AgentSpecLoader(tool_registry=tool_registry).load_component(search_flow)
            conversation = executable_flow.start_conversation({
                "user_query": user_query,
                "semantic_ratio": str(semantic_ratio),
                "limit": str(limit)
            })
            status = conversation.execute()
            
            # Parse the response
            response_json = status.output_values.get("response", "{}")
            response_data = json.loads(response_json)
            
            answer = response_data.get("answer", "")
            citations = response_data.get("citations", [])
            
            print(f"Chat completed - Answer length: {len(answer)}, Citations: {len(citations)}")
            
            return {
                "answer": answer,
                "citations": citations,
                "documents_found": len(citations)
            }
        
    except Exception as e:
        print(f"Error in chat flow: {e}")
        return {
            "answer": f"I encountered an error while processing your question: {str(e)}",
            "citations": [],
            "documents_found": 0
        }
