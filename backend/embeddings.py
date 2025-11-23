import os
from typing import List, Optional
from dotenv import load_dotenv
from together import Together

# Load Together AI API key
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, "api.env")
load_dotenv(env_path)

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY") or os.getenv("OPENAI_API_KEY")

# Initialize Together AI client
client = Together(api_key=TOGETHER_API_KEY) if TOGETHER_API_KEY else None

def generate_embedding(text: str) -> Optional[List[float]]:
    """
    Generate embeddings using Together AI's embedding model.
    
    Args:
        text: Text to generate embeddings for
        
    Returns:
        List of floats representing the embedding vector, or None if failed
    """
    if not client:
        print("Warning: No Together AI API key found")
        return None
    
    if not text or not text.strip():
        print("Warning: Empty text provided for embedding")
        return None
    
    try:
        response = client.embeddings.create(
            model="Alibaba-NLP/gte-modernbert-base",
            input=text
        )
        
        if response.data and len(response.data) > 0:
            embedding = response.data[0].embedding
            print(f"Generated embedding with {len(embedding)} dimensions")
            return embedding
        else:
            print(f"Unexpected response format: {response}")
            return None
            
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None
