"""
Embedding generation utilities with batching support.
"""
import os
from typing import List
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

# Check if we're in production
is_production = os.getenv("ENVIRONMENT") == "production"

if not is_production:
    # Development: prioritize .env file
    project_root = Path(__file__).resolve().parent.parent
    dotenv_path = project_root / '.env'
    load_dotenv(dotenv_path, override=True)
else:
    # Production: use cloud platform env vars only
    load_dotenv()

# Initialize OpenAI client
api_key = os.getenv("EMBEDDING_API_KEY", "") or "ollama"
openai_client = OpenAI(api_key=api_key, base_url=os.getenv("EMBEDDING_BASE_URL"))


def create_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Create embeddings for a list of text chunks using OpenAI.
    Batches requests to avoid token limits.
    
    Args:
        texts: List of text chunks to embed
        
    Returns:
        List of embedding vectors
    """
    if not texts:
        return []
    
    # Configuration for batching
    MAX_BATCH_SIZE = 100  # Maximum number of texts per batch
    MAX_TOKENS_PER_BATCH = 250000  # Leave some buffer below the 300k limit
    
    # Rough estimation: 1 token ≈ 4 characters for English text
    def estimate_tokens(text: str) -> int:
        return len(text) // 4
    
    all_embeddings = []
    current_batch = []
    current_tokens = 0
    
    for text in texts:
        text_tokens = estimate_tokens(text)
        
        # Check if adding this text would exceed limits
        if (len(current_batch) >= MAX_BATCH_SIZE or 
            (current_tokens + text_tokens > MAX_TOKENS_PER_BATCH and current_batch)):
            
            # Process current batch
            try:
                print(f"Creating embeddings for batch of {len(current_batch)} texts (~{current_tokens} tokens)...")
                response = openai_client.embeddings.create(
                    model=os.getenv("EMBEDDING_MODEL_CHOICE"),
                    input=current_batch
                )
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
                
                # Reset for next batch
                current_batch = []
                current_tokens = 0
            except Exception as e:
                print(f"Error creating embeddings for batch: {e}")
                # Return what we have so far plus zero vectors for failed items
                zero_vector = [0] * 1536  # Default dimension for text-embedding-3-small
                all_embeddings.extend([zero_vector] * len(current_batch))
                current_batch = []
                current_tokens = 0
        
        current_batch.append(text)
        current_tokens += text_tokens
    
    # Process remaining batch
    if current_batch:
        try:
            print(f"Creating embeddings for final batch of {len(current_batch)} texts (~{current_tokens} tokens)...")
            response = openai_client.embeddings.create(
                model=os.getenv("EMBEDDING_MODEL_CHOICE"),
                input=current_batch
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
        except Exception as e:
            print(f"Error creating embeddings for final batch: {e}")
            zero_vector = [0] * 1536
            all_embeddings.extend([zero_vector] * len(current_batch))
    
    print(f"Created {len(all_embeddings)} embeddings total")
    return all_embeddings
