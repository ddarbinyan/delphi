import warnings
warnings.filterwarnings('ignore')

from pyagentspec.llms import OpenAiCompatibleConfig, LlmGenerationConfig

import os
from dotenv import load_dotenv

load_dotenv()
together_ai_api_key = os.getenv('OPENAI_API_KEY')

llm_config = OpenAiCompatibleConfig(
    # name="openai/gpt-oss-120B",
    # model_id="openai/gpt-oss-120B",
    name="Qwen/Qwen2.5-VL-72B-Instruct",
    model_id="Qwen/Qwen2.5-VL-72B-Instruct",
    url="https://api.together.xyz/v1/chat/completions/",
    default_generation_parameters=LlmGenerationConfig(
        max_tokens=512,
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

# Define the tool that performs image analysis
def analyze_image(image_path_str: str) -> str:
    # Load image
    image_path = Path(image_path_str)
    if not image_path.exists():
        # Fallback if running from delphi directory
        if Path("delphi").exists():
             image_path = Path("delphi") / image_path_str
        elif Path("resources").exists():
             image_path = Path("resources") / Path(image_path_str).name
    
    if not image_path.exists():
        return json.dumps({"status": "error", "message": f"Image not found at {image_path_str}"})

    image_bytes = image_path.read_bytes()
    image_content = ImageContent.from_bytes(image_bytes, format="png")

    # Create prompt with image
    prompt = Prompt(messages=[
        Message(
            role="user",
            contents=[
                TextContent(content="Extract all text from this image. Return only the extracted text. If no text is visible, return 'NO_TEXT_FOUND'."),
                image_content
            ]
        )
    ])

    # We need to load the LLM inside the tool or pass it. 
    # For simplicity in this script, we use the global llm_config but we need to load it.
    # In a real app, the LLM might be injected or loaded once.
    llm_component = AgentSpecLoader().load_component(llm_config)
    completion = llm_component.generate(prompt)
    extracted_text = completion.message.content.strip()

    if extracted_text == "NO_TEXT_FOUND" or not extracted_text:
        return json.dumps({"status": "error", "message": "No text detected in the image."})

    # Determine output path
    # We want to store it in resources/extracted_text/<image_name>/
    # Try to find the resources directory relative to the image or the script
    if "resources" in image_path.parts:
        # If image is in .../resources/..., go up until we find resources
        resources_idx = image_path.parts.index("resources")
        resources_dir = Path(*image_path.parts[:resources_idx+1])
    else:
        # Fallback to local resources dir
        resources_dir = Path("resources")
        if not resources_dir.exists() and Path("delphi/resources").exists():
            resources_dir = Path("delphi/resources")
    
    if not resources_dir.exists():
         # Create local resources if not found
         resources_dir = Path("resources")
         resources_dir.mkdir(exist_ok=True)

    # Create organized structure: resources/extracted_text/<image_name>/
    output_dir = resources_dir / "extracted_text" / image_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{timestamp}.txt"
    output_file = output_dir / output_filename
    
    output_file.write_text(extracted_text, encoding="utf-8")

    return json.dumps({
        "status": "success", 
        "path": str(output_file),
        "original_image": str(image_path)
    })

# Define the ServerTool spec
analyze_image_tool = ServerTool(
    name="analyze_image",
    description="Extracts text from an image and saves it to a file.",
    inputs=[StringProperty(title="image_path", description="Path to the image file")],
    outputs=[StringProperty(title="result_json", description="JSON string containing status and path to extracted text")]
)

# Define the Flow
start_node = StartNode(
    name="start",
    inputs=[StringProperty(title="image_path", description="Path to the image")]
)

tool_node = ToolNode(
    name="image_analysis_node",
    tool=analyze_image_tool
)

end_node = EndNode(
    name="end",
    outputs=[StringProperty(title="result", description="Final result")]
)

flow = Flow(
    name="Image Analysis Flow",
    start_node=start_node,
    nodes=[start_node, tool_node, end_node],
    control_flow_connections=[
        ControlFlowEdge(name="start_to_tool", from_node=start_node, to_node=tool_node),
        ControlFlowEdge(name="tool_to_end", from_node=tool_node, to_node=end_node),
    ],
    data_flow_connections=[
        DataFlowEdge(
            name="path_edge",
            source_node=start_node,
            source_output="image_path",
            destination_node=tool_node,
            destination_input="image_path"
        ),
        DataFlowEdge(
            name="result_edge",
            source_node=tool_node,
            source_output="result_json",
            destination_node=end_node,
            destination_input="result"
        )
    ]
)

# Register the tool implementation
tool_registry = {
    "analyze_image": analyze_image
}

# Execute the flow
print("Executing Flow...")
executable_flow = AgentSpecLoader(tool_registry=tool_registry).load_component(flow)
conversation = executable_flow.start_conversation({"image_path": "delphi/resources/sample-1.png"})
status = conversation.execute()

print("Flow Result:")
print(status.output_values["result"])
