import warnings
warnings.filterwarnings('ignore')
import argparse
import sys

from pyagentspec.llms import OpenAiCompatibleConfig, LlmGenerationConfig

import os
from dotenv import load_dotenv

# Get the directory where this script is located
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, "api.env")
load_dotenv(env_path)

llm_config = OpenAiCompatibleConfig(
    name="Qwen/Qwen2.5-VL-72B-Instruct",
    model_id="Qwen/Qwen2.5-VL-72B-Instruct",
    url="https://api.together.xyz/v1/chat/completions/",
    default_generation_parameters=LlmGenerationConfig(
        temperature=0.7,
        top_p=0.95,
    )
)

from wayflowcore.agentspec import AgentSpecLoader
from wayflowcore.messagelist import Message, TextContent, ImageContent
from wayflowcore.models import Prompt
from pathlib import Path
from pyagentspec.flows.flow import Flow
from pyagentspec.flows.nodes import StartNode, EndNode, ToolNode
from pyagentspec.flows.edges import ControlFlowEdge, DataFlowEdge
from pyagentspec.tools import ServerTool
from pyagentspec.property import StringProperty
import json
from datetime import datetime

from .prompt import SYSTEM_PROMPT_INIT, SUMMARIZATION_PROMPT, REMINDER_ANALYSIS_PROMPT

# Define the tool that performs image analysis
def analyze_image(image_path: str) -> str:
    # Load image
    image_path_obj = Path(image_path)
    image_bytes = image_path_obj.read_bytes()
    
    # Determine format based on extension
    ext = image_path_obj.suffix.lower().replace('.', '')
    if ext == 'jpg': ext = 'jpeg'
    
    image_content = ImageContent.from_bytes(image_bytes, format=ext)

    # Create prompt with image
    prompt = Prompt(messages=[
        Message(
            role="system",
            contents=[TextContent(content=SYSTEM_PROMPT_INIT)]
        ),
        Message(
            role="user",
            contents=[
                TextContent(content="Extract the text from this document."),
                image_content
            ]
        )
    ])


    llm_component = AgentSpecLoader().load_component(llm_config)
    completion = llm_component.generate(prompt)
    extracted_text = completion.message.content.strip()

    if extracted_text == "NO_TEXT_FOUND" or not extracted_text:
        print("No text detected in the image.")
        return ""
    
    return extracted_text


# Define the tool that summarizes text and extracts keywords
def summarize_and_extract_keywords(extracted_text: str) -> str:
    """
    Summarizes the extracted text and generates keywords.
    Returns JSON string with summary and keywords.
    """
    if not extracted_text or len(extracted_text.strip()) < 10:
        # Return empty result for very short text
        return json.dumps({"summary": "", "keywords": []})
    
    # Create prompt for summarization
    prompt = Prompt(messages=[
        Message(
            role="system",
            contents=[TextContent(content=SUMMARIZATION_PROMPT)]
        ),
        Message(
            role="user",
            contents=[TextContent(content=f"Document text:\n\n{extracted_text}")]
        )
    ])
    
    llm_component = AgentSpecLoader().load_component(llm_config)
    completion = llm_component.generate(prompt)
    result = completion.message.content.strip()
    
    # Try to parse the JSON response
    try:
        # Remove markdown code blocks if present
        if result.startswith("```"):
            result = result.split("```")[1]
            if result.startswith("json"):
                result = result[4:]
        
        parsed = json.loads(result)
        return json.dumps(parsed)
    except json.JSONDecodeError as e:
        print(f"Failed to parse summarization response: {e}")
        print(f"Response was: {result}")
        # Return a fallback structure
        return json.dumps({"summary": "", "keywords": []})


# Define the tool that analyzes for reminders
def analyze_for_reminder(extracted_text: str, filename: str, analysis_result: str) -> str:
    """
    Analyzes the document to determine if it requires action and creates reminder data.
    Returns JSON string with reminder information.
    """
    if not extracted_text or len(extracted_text.strip()) < 10:
        # Return empty result for very short text
        return json.dumps({"requires_action": False, "category": None, "due_date": None, "action_title": None, "action_description": None})
    
    # Parse the analysis result to get keywords
    try:
        analysis = json.loads(analysis_result)
        keywords = analysis.get("keywords", [])
        summary = analysis.get("summary", "")
    except json.JSONDecodeError:
        keywords = []
        summary = ""
    
    # Create prompt for reminder analysis
    document_info = f"""Document: {filename}
Content: {extracted_text[:2000]}
Summary: {summary}
Keywords: {', '.join(keywords) if keywords else 'None'}"""
    
    prompt = Prompt(messages=[
        Message(
            role="system",
            contents=[TextContent(content=REMINDER_ANALYSIS_PROMPT)]
        ),
        Message(
            role="user",
            contents=[TextContent(content=document_info)]
        )
    ])
    
    llm_component = AgentSpecLoader().load_component(llm_config)
    completion = llm_component.generate(prompt)
    result = completion.message.content.strip()
    
    # Try to parse the JSON response
    try:
        # Remove markdown code blocks if present
        if result.startswith("```"):
            result = result.split("```")[1]
            if result.startswith("json"):
                result = result[4:]
        
        parsed = json.loads(result)
        return json.dumps(parsed)
    except json.JSONDecodeError as e:
        print(f"Failed to parse reminder analysis response: {e}")
        print(f"Response was: {result}")
        # Return a fallback structure
        return json.dumps({"requires_action": False, "category": None, "due_date": None, "action_title": None, "action_description": None})


analyze_image_tool = ServerTool(
    name="analyze_image",
    description="Extracts text from an image and saves it to a file.",
    inputs=[StringProperty(title="image_path", description="Path to the image file")],
    outputs=[StringProperty(title="extracted_text", description="Extracted text from the image")]
)

summarize_tool = ServerTool(
    name="summarize_and_extract_keywords",
    description="Summarizes text and extracts keywords.",
    inputs=[StringProperty(title="extracted_text", description="Text to summarize")],
    outputs=[StringProperty(title="analysis_result", description="JSON with summary and keywords")]
)

reminder_tool = ServerTool(
    name="analyze_for_reminder",
    description="Analyzes document for actionable items and deadlines.",
    inputs=[
        StringProperty(title="extracted_text", description="Extracted text from document"),
        StringProperty(title="filename", description="Document filename"),
        StringProperty(title="analysis_result", description="Analysis result with summary and keywords")
    ],
    outputs=[StringProperty(title="reminder_data", description="JSON with reminder information")]
)

# Define the Flow with summarization and reminder analysis
start_node = StartNode(
    name="start",
    inputs=[
        StringProperty(title="image_path", description="Path to the image"),
        StringProperty(title="filename", description="Document filename")
    ]
)

extraction_node = ToolNode(
    name="extraction_node",
    tool=analyze_image_tool
)

summarization_node = ToolNode(
    name="summarization_node",
    tool=summarize_tool
)

reminder_node = ToolNode(
    name="reminder_node",
    tool=reminder_tool
)

end_node = EndNode(
    name="end",
    outputs=[
        StringProperty(title="text", description="Extracted text"),
        StringProperty(title="analysis", description="Summary and keywords JSON"),
        StringProperty(title="reminder", description="Reminder information JSON")
    ]
)

flow = Flow(
    name="Document Processing Flow",
    start_node=start_node,
    nodes=[start_node, extraction_node, summarization_node, reminder_node, end_node],
    control_flow_connections=[
        ControlFlowEdge(name="start_to_extraction", from_node=start_node, to_node=extraction_node),
        ControlFlowEdge(name="extraction_to_summarization", from_node=extraction_node, to_node=summarization_node),
        ControlFlowEdge(name="summarization_to_reminder", from_node=summarization_node, to_node=reminder_node),
        ControlFlowEdge(name="reminder_to_end", from_node=reminder_node, to_node=end_node),
    ],
    data_flow_connections=[
        DataFlowEdge(
            name="path_edge",
            source_node=start_node,
            source_output="image_path",
            destination_node=extraction_node,
            destination_input="image_path"
        ),
        DataFlowEdge(
            name="text_to_summarization",
            source_node=extraction_node,
            source_output="extracted_text",
            destination_node=summarization_node,
            destination_input="extracted_text"
        ),
        DataFlowEdge(
            name="text_to_reminder",
            source_node=extraction_node,
            source_output="extracted_text",
            destination_node=reminder_node,
            destination_input="extracted_text"
        ),
        DataFlowEdge(
            name="filename_to_reminder",
            source_node=start_node,
            source_output="filename",
            destination_node=reminder_node,
            destination_input="filename"
        ),
        DataFlowEdge(
            name="analysis_to_reminder",
            source_node=summarization_node,
            source_output="analysis_result",
            destination_node=reminder_node,
            destination_input="analysis_result"
        ),
        DataFlowEdge(
            name="text_to_end",
            source_node=extraction_node,
            source_output="extracted_text",
            destination_node=end_node,
            destination_input="text"
        ),
        DataFlowEdge(
            name="analysis_to_end",
            source_node=summarization_node,
            source_output="analysis_result",
            destination_node=end_node,
            destination_input="analysis"
        ),
        DataFlowEdge(
            name="reminder_to_end",
            source_node=reminder_node,
            source_output="reminder_data",
            destination_node=end_node,
            destination_input="reminder"
        )
    ]
)

# Register the tool implementations
tool_registry = {
    "analyze_image": analyze_image,
    "summarize_and_extract_keywords": summarize_and_extract_keywords,
    "analyze_for_reminder": analyze_for_reminder
}

def process_document(file_path: str, filename: str = None) -> dict:
    """
    Process a document (image) using the AI agent flow to extract text, summarize, extract keywords, and analyze for reminders.
    
    Returns:
        dict with keys: 'text', 'summary', 'keywords', 'reminder_data'
    """
    try:
        # Extract filename from path if not provided
        if filename is None:
            filename = Path(file_path).name
        
        executable_flow = AgentSpecLoader(tool_registry=tool_registry).load_component(flow)
        conversation = executable_flow.start_conversation({
            "image_path": file_path,
            "filename": filename
        })
        status = conversation.execute()
        
        extracted_text = status.output_values.get("text", "")
        analysis_json = status.output_values.get("analysis", "{}")
        reminder_json = status.output_values.get("reminder", "{}")
        
        # Parse the analysis JSON
        try:
            analysis = json.loads(analysis_json)
            summary = analysis.get("summary", "")
            keywords = analysis.get("keywords", [])
        except json.JSONDecodeError:
            print(f"Failed to parse analysis JSON: {analysis_json}")
            summary = ""
            keywords = []
        
        # Parse the reminder JSON
        try:
            reminder_data = json.loads(reminder_json)
        except json.JSONDecodeError:
            print(f"Failed to parse reminder JSON: {reminder_json}")
            reminder_data = {}
        
        print(f"Extracted text: {extracted_text[:200]}...")
        print(f"Summary: {summary}")
        print(f"Keywords: {', '.join(keywords)}")
        print(f"Reminder data: {reminder_data}")
        
        return {
            "text": extracted_text,
            "summary": summary,
            "keywords": keywords,
            "reminder_data": reminder_data
        }
        
    except Exception as e:
        print(f"Error processing document with AI agent: {e}")
        return {
            "text": "",
            "summary": "",
            "keywords": [],
            "reminder_data": {}
        }