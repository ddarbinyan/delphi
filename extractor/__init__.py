import base64
import os
from pathlib import Path
import tempfile
from prompt import SYSTEM_PROMPT_INIT, SYSTEM_PROMPT_FOLLOW
from pdf2image import convert_from_path
from openai import OpenAI
PAGE_DELIMITER='\n\n'

def extract_pdf_pages(pdf_file: Path, client: OpenAI) -> str:
    """
    Converts PDF pages to images and processes them with OpenAI compatible vision model.
    
    Args:
        pdf_file: File path to the PDF or file object
        client: OpenAI client
    
    Returns:
        list: Responses from OpenAI API for each page
    """
    
    # Convert PDF pages to images
    images = convert_from_path(pdf_file)
    
    responses = ""
    
    for i, image in enumerate(images):
        # Create secure temporary file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            temp_path = temp_file.name
            image.save(temp_path, "PNG")
        
        try:
            # Encode image to base64
            with open(temp_path, "rb") as img_file:
                base64_image = base64.b64encode(img_file.read()).decode('utf-8')
            
            if i == 0:
                prompt = SYSTEM_PROMPT_INIT
                additional = []
            else:
                prompt = SYSTEM_PROMPT_FOLLOW
                additional = [{
                    "type": "text",
                    "text": responses
                }]
            
            # Call OpenAI API
            response = client.chat.completions.create(
                model="Qwen/Qwen2.5-VL-72B-Instruct",
                messages=[
                    {
                        "role": "system",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            },
                            *additional
                        ]
                    }
                ]
            )
            responses += PAGE_DELIMITER
            responses += response.choices[0].message.content
        finally:
            # Clean up temp file
            os.remove(temp_path)
    
    return responses

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url="https://api.together.xyz/v1"
)
extract_pdf_pages(pdf_file='./sample-local-pdf.pdf', client=client)