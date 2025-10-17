"""
Advanced text chunking with Markdown awareness and semantic splitting.
Matches the n8n JavaScript implementation with LLM-guided breakpoints.
"""
import os
import re
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

from .text_sanitizer import sanitize_text, clean_text
from .markdown_parser import split_by_headings, split_markdown_into_blocks

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

# Chunking configuration (matching n8n defaults)
MAX_CHUNK_SIZE = 1000
MIN_CHUNK_SIZE = 400
MERGE_PAD = int(MAX_CHUNK_SIZE * 1.05)
ENABLE_HEADING_SPLIT = True

# Initialize LLM client for chunking (if configured)
_llm_client: Optional[OpenAI] = None

def get_llm_client() -> Optional[OpenAI]:
    """Get or initialize the LLM client for chunking."""
    global _llm_client
    
    if _llm_client is not None:
        return _llm_client
    
    # Check if LLM chunking is configured (reuse main LLM credentials)
    base_url = os.getenv('CHUNKING_LLM_BASE_URL') or os.getenv('LLM_BASE_URL')
    api_key = os.getenv('CHUNKING_LLM_API_KEY') or os.getenv('LLM_API_KEY')
    
    if not base_url or not api_key:
        return None
    
    try:
        _llm_client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        return _llm_client
    except Exception as e:
        print(f"Warning: Failed to initialize LLM client for chunking: {e}")
        return None


def llm_breakpoint_sync(first_window: str, max_chars: int) -> int:
    """
    LLM-guided breakpoint detection (matches n8n implementation).
    Uses LLM to find natural topic transitions, falls back to sentence boundaries.
    
    Args:
        first_window: Text window to analyze
        max_chars: Maximum character position for the break
        
    Returns:
        Character position for the break
    """
    # Try LLM-guided breakpoint if configured
    client = get_llm_client()
    model = os.getenv('CHUNKING_LLM_MODEL', 'gpt-4o-mini')
    
    if client and model:
        try:
            # LLM prompt matching the n8n implementation
            prompt = f"""You are analyzing a document to find the best transition point to split it into meaningful sections.

Your goal: Keep related content together and split where topics naturally transition.

Read this text carefully and identify where one topic/section ends and another begins:

{first_window}

Find the best transition point that occurs BEFORE character position {max_chars}.

Look for:
- Section headings or topic changes
- Paragraph boundaries where the subject shifts
- Complete conclusions before new ideas start
- Natural breaks between different aspects of the content

Output the LAST WORD that appears right before your chosen split point.
Just the single word itself, nothing else."""

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=50
            )
            
            break_word = response.choices[0].message.content.strip()
            
            if break_word:
                # Find the last occurrence of this word before max_chars
                idx = first_window.rfind(break_word, 0, max_chars)
                if idx != -1:
                    # Move to the end of the word
                    breakpoint = idx + len(break_word)
                    
                    # Skip trailing punctuation and one space
                    while breakpoint < len(first_window) and first_window[breakpoint] in '.!?,;: ':
                        breakpoint += 1
                        if breakpoint > 0 and first_window[breakpoint - 1] == ' ':
                            break
                    
                    breakpoint = min(breakpoint, max_chars)
                    print(f"LLM-guided breakpoint at position {breakpoint} (word: '{break_word}')")
                    return breakpoint
        
        except Exception as e:
            print(f"LLM breakpoint detection failed, falling back to sentence boundary: {e}")
    
    # Fallback: Find the last sentence ending before max_chars
    window = first_window[:max_chars]
    
    # Look for sentence endings
    sentence_endings = [m.end() for m in re.finditer(r'[.!?]\s+', window)]
    if sentence_endings:
        return sentence_endings[-1]
    
    # If no sentence ending, look for paragraph break
    paragraph_breaks = [m.end() for m in re.finditer(r'\n\n', window)]
    if paragraph_breaks:
        return paragraph_breaks[-1]
    
    # Final fallback: return max_chars
    return max_chars


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 0, use_advanced: bool = True) -> List[str]:
    """
    Advanced text chunking with Markdown awareness, table preservation, and semantic splitting.
    
    This function implements a sophisticated chunking strategy:
    - Sanitizes LaTeX/escape noise
    - Preserves Markdown structure (especially pipe tables)
    - Treats tables as atomic blocks (never splits inside)
    - Uses intelligent breakpoints for long prose
    - Merges small chunks with neighbors (but never merges tables)
    
    Args:
        text: The text to chunk
        chunk_size: Target maximum characters per chunk (default: 1000)
        overlap: Overlap between chunks (ignored in advanced mode, kept for compatibility)
        use_advanced: Whether to use advanced chunking (default: True)
        
    Returns:
        List of text chunks
    """
    if not text:
        return []
    
    # For backwards compatibility, offer simple chunking
    if not use_advanced:
        text = text.replace('\r', '')
        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunk = text[i:i + chunk_size]
            if chunk:
                chunks.append(chunk)
        return chunks
    
    # Advanced chunking pipeline
    max_size = chunk_size or MAX_CHUNK_SIZE
    min_size = min(MIN_CHUNK_SIZE, max_size // 2)
    merge_pad = int(max_size * 1.05)
    
    # 1. Sanitize and clean
    sanitized = sanitize_text(text)
    cleaned = clean_text(sanitized)
    
    # 2. Detect if markdown-ish (has headings or tables)
    has_heading = bool(re.search(r'(^|\n)#{1,6}\s+\S', cleaned))
    has_table = bool(re.search(r'\n\|[^|\n]+\|', cleaned)) and bool(re.search(r'\|.*\|', cleaned))
    is_markdownish = has_heading or has_table
    
    # 3. Split into blocks
    blocks = [{'text': cleaned, 'is_table': False}]
    if is_markdownish:
        md_blocks = split_markdown_into_blocks(cleaned)
        
        if ENABLE_HEADING_SPLIT:
            # Further split non-table blocks by headings
            split_further = []
            for blk in md_blocks:
                if blk['is_table']:
                    split_further.append(blk)
                    continue
                parts = split_by_headings(blk['text'])
                if len(parts) > 1:
                    split_further.extend([{'text': t, 'is_table': False} for t in parts])
                else:
                    split_further.append(blk)
            md_blocks = split_further
        
        blocks = md_blocks
    
    # 4. Build chunks from blocks
    chunks = []
    
    for blk in blocks:
        content = blk['text'].strip()
        if not content:
            continue
        
        # Keep tables atomic (never split inside)
        if blk.get('is_table'):
            chunks.append({'content': content, 'is_table': True})
            continue
        
        # Non-table text block
        if len(content) <= max_size:
            chunks.append({'content': content, 'is_table': False})
        else:
            # For long prose blocks, split using sentence boundaries
            remaining = content
            while remaining:
                if len(remaining) <= max_size:
                    chunks.append({'content': remaining.strip(), 'is_table': False})
                    break
                
                window = remaining[:max_size]
                bp = llm_breakpoint_sync(window, max_size)
                piece = remaining[:bp].strip()
                
                if piece:
                    chunks.append({'content': piece, 'is_table': False})
                
                remaining = remaining[bp:].strip()
    
    # 5. Merge small chunks with neighbors (allow small overflow, but NEVER merge tables)
    i = 0
    while i < len(chunks):
        cur = chunks[i]
        cur_size = len(cur['content'])
        
        if cur_size < min_size and not cur.get('is_table'):
            # Try forward merge
            if i + 1 < len(chunks) and not chunks[i + 1].get('is_table'):
                next_size = len(chunks[i + 1]['content'])
                if cur_size + next_size <= merge_pad:
                    cur['content'] += '\n\n' + chunks[i + 1]['content']
                    chunks.pop(i + 1)
                    continue
            
            # Try backward merge
            if i > 0 and not chunks[i - 1].get('is_table'):
                prev_size = len(chunks[i - 1]['content'])
                if prev_size + cur_size <= merge_pad:
                    chunks[i - 1]['content'] += '\n\n' + cur['content']
                    chunks.pop(i)
                    i -= 1
                    continue
        
        i += 1
    
    # 6. Extract just the content strings
    return [chunk['content'] for chunk in chunks]
