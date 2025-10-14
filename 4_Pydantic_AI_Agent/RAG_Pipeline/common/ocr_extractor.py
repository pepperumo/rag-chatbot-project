"""
Document text extraction using Mistral OCR API.
Supports PDFs and images (PNG, JPG, JPEG, SVG).
"""
import os
import requests
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
project_root = Path(__file__).resolve().parent.parent.parent
dotenv_path = project_root / '.env'
load_dotenv(dotenv_path, override=True)


def extract_text_with_ocr(file_content: bytes, file_name: str = "document", mime_type: str = "application/pdf") -> str:
    """
    Extract text from a PDF or image file using Mistral OCR API.
    
    This function follows the n8n workflow pattern:
    1. Upload file to Mistral API (POST /v1/files)
    2. Get URL for the uploaded file (GET /v1/files/{id}/url)
    3. Process with OCR (POST /v1/ocr)
    
    Supported formats:
    - PDFs: application/pdf
    - Images: image/png, image/jpg, image/jpeg, image/svg
    
    Args:
        file_content: Binary content of the file
        file_name: Name of the file (default: "document")
        mime_type: MIME type of the file (default: "application/pdf")
        
    Returns:
        Extracted text from the document using Mistral OCR
    """
    # Get Mistral API configuration from environment
    mistral_api_key = os.getenv('LLM_OCR_API_KEY')
    mistral_base_url = os.getenv('LLM_OCR_URL', 'https://api.mistral.ai/v1')
    
    if not mistral_api_key:
        print("Warning: LLM_OCR_API_KEY not set, falling back to filename")
        return file_name
    
    try:
        # Step 1: Upload file to Mistral
        upload_url = f"{mistral_base_url.replace('/ocr', '')}/files"
        headers = {
            'Authorization': f'Bearer {mistral_api_key}'
        }
        
        files = {
            'file': (file_name, file_content, mime_type)
        }
        data = {
            'purpose': 'ocr'
        }
        
        print(f"Uploading {mime_type} file to Mistral API...")
        upload_response = requests.post(upload_url, headers=headers, files=files, data=data)
        upload_response.raise_for_status()
        upload_data = upload_response.json()
        file_id = upload_data.get('id')
        
        if not file_id:
            raise Exception("No file ID returned from upload")
        
        print(f"File uploaded successfully, ID: {file_id}")
        
        # Step 2: Get URL for the uploaded file
        url_endpoint = f"{mistral_base_url.replace('/ocr', '')}/files/{file_id}/url"
        url_params = {'expiry': '24'}  # 24 hours expiry
        
        print(f"Getting file URL...")
        url_response = requests.get(url_endpoint, headers=headers, params=url_params)
        url_response.raise_for_status()
        url_data = url_response.json()
        document_url = url_data.get('url')
        
        if not document_url:
            raise Exception("No document URL returned")
        
        print(f"Document URL obtained")
        
        # Step 3: Process with OCR
        ocr_url = mistral_base_url if mistral_base_url.endswith('/ocr') else f"{mistral_base_url}/ocr"
        ocr_payload = {
            'model': 'mistral-ocr-latest',
            'document': {
                'type': 'document_url',
                'document_url': document_url
            },
            'include_image_base64': True
        }
        
        print(f"Processing document with Mistral OCR...")
        ocr_response = requests.post(ocr_url, headers=headers, json=ocr_payload)
        ocr_response.raise_for_status()
        ocr_data = ocr_response.json()
        
        # Extract text from OCR response
        extracted_text = ""
        
        # Try to extract text from various possible response structures
        if isinstance(ocr_data, dict):
            # Check for 'text' field
            if 'text' in ocr_data:
                extracted_text = ocr_data['text']
            # Check for 'content' field
            elif 'content' in ocr_data:
                extracted_text = ocr_data['content']
            # Check for 'pages' array
            elif 'pages' in ocr_data and isinstance(ocr_data['pages'], list):
                page_texts = []
                for page in ocr_data['pages']:
                    if isinstance(page, dict):
                        page_text = page.get('text', page.get('content', ''))
                        if page_text:
                            page_texts.append(page_text)
                extracted_text = "\n\n".join(page_texts)
            # Check for 'result' field
            elif 'result' in ocr_data:
                result = ocr_data['result']
                if isinstance(result, str):
                    extracted_text = result
                elif isinstance(result, dict):
                    extracted_text = result.get('text', result.get('content', ''))
            # Check for markdown or data field
            elif 'markdown' in ocr_data:
                extracted_text = ocr_data['markdown']
            elif 'data' in ocr_data:
                extracted_text = ocr_data['data']
        
        # If still no text, try to convert the entire response to string
        if not extracted_text:
            print(f"Warning: Could not find text in expected fields. Response keys: {ocr_data.keys() if isinstance(ocr_data, dict) else 'not a dict'}")
            # Try extracting from choices (ChatGPT-style response)
            if isinstance(ocr_data, dict) and 'choices' in ocr_data:
                choices = ocr_data['choices']
                if isinstance(choices, list) and len(choices) > 0:
                    first_choice = choices[0]
                    if isinstance(first_choice, dict):
                        message = first_choice.get('message', {})
                        extracted_text = message.get('content', '')
            
            # Final fallback
            if not extracted_text:
                extracted_text = str(ocr_data)
        
        print(f"OCR completed successfully, extracted {len(extracted_text)} characters")
        return extracted_text
        
    except requests.exceptions.RequestException as e:
        print(f"Error during Mistral OCR API request: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text[:500]}")
        # Fallback to filename
        return file_name
    except Exception as e:
        print(f"Unexpected error during document extraction with Mistral OCR: {e}")
        # Fallback to filename
        return file_name


# Backward compatibility wrapper for PDFs
def extract_text_from_pdf(file_content: bytes, file_name: str = "document.pdf") -> str:
    """
    Legacy wrapper for PDF extraction. Use extract_text_with_ocr() instead.
    
    Args:
        file_content: Binary content of the PDF file
        file_name: Name of the PDF file
        
    Returns:
        Extracted text from the PDF
    """
    return extract_text_with_ocr(file_content, file_name, "application/pdf")
