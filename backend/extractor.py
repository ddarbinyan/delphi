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

from .prompt import SYSTEM_PROMPT_INIT, SUMMARIZATION_PROMPT

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

# Define the Flow with summarization
start_node = StartNode(
    name="start",
    inputs=[StringProperty(title="image_path", description="Path to the image")]
)

extraction_node = ToolNode(
    name="extraction_node",
    tool=analyze_image_tool
)

summarization_node = ToolNode(
    name="summarization_node",
    tool=summarize_tool
)

end_node = EndNode(
    name="end",
    outputs=[
        StringProperty(title="text", description="Extracted text"),
        StringProperty(title="analysis", description="Summary and keywords JSON")
    ]
)

flow = Flow(
    name="Document Processing Flow",
    start_node=start_node,
    nodes=[start_node, extraction_node, summarization_node, end_node],
    control_flow_connections=[
        ControlFlowEdge(name="start_to_extraction", from_node=start_node, to_node=extraction_node),
        ControlFlowEdge(name="extraction_to_summarization", from_node=extraction_node, to_node=summarization_node),
        ControlFlowEdge(name="summarization_to_end", from_node=summarization_node, to_node=end_node),
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
        )
    ]
)

# Register the tool implementations
tool_registry = {
    "analyze_image": analyze_image,
    "summarize_and_extract_keywords": summarize_and_extract_keywords
}

def process_document(file_path: str) -> dict:
    """
    Process a document (image) using the AI agent flow to extract text, summarize, and extract keywords.
    
    Returns:
        dict with keys: 'text', 'summary', 'keywords'
    """
    try:
        executable_flow = AgentSpecLoader(tool_registry=tool_registry).load_component(flow)
        conversation = executable_flow.start_conversation({"image_path": file_path})
        status = conversation.execute()
        
        extracted_text = status.output_values.get("text", "")
        analysis_json = status.output_values.get("analysis", "{}")
        
        # Parse the analysis JSON
        try:
            analysis = json.loads(analysis_json)
            summary = analysis.get("summary", "")
            keywords = analysis.get("keywords", [])
        except json.JSONDecodeError:
            print(f"Failed to parse analysis JSON: {analysis_json}")
            summary = ""
            keywords = []
        
        print(f"Extracted text: {extracted_text[:200]}...")
        print(f"Summary: {summary}")
        print(f"Keywords: {', '.join(keywords)}")
        
        return {
            "text": extracted_text,
            "summary": summary,
            "keywords": keywords
        }
        
    except Exception as e:
        print(f"Error processing document with AI agent: {e}")
        return {
            "text": "",
            "summary": "",
            "keywords": []
        }