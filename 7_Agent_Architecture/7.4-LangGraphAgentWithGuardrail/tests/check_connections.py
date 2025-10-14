#!/usr/bin/env python3
"""
Test script to verify API connections and configuration.
"""
import asyncio
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from supabase import Client
import httpx
from clients import get_agent_clients

load_dotenv()

async def test_openai_connection():
    """Test OpenAI API connection"""
    print("Testing OpenAI API connection...")
    
    api_key = os.getenv('LLM_API_KEY')
    base_url = os.getenv('LLM_BASE_URL', 'https://api.openai.com/v1')
    
    if not api_key or api_key == 'no-api-key-provided':
        print("❌ No valid OpenAI API key found")
        return False
    
    try:
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        
        # Test with a simple completion
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'API connection test successful'"}],
            max_tokens=20
        )
        
        print("✅ OpenAI API connection successful")
        print(f"Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API connection failed: {str(e)}")
        if "401" in str(e):
            print("   This usually means the API key is invalid or expired")
        elif "429" in str(e):
            print("   Rate limit exceeded")
        elif "ReadError" in str(e):
            print("   Network connection issue")
        return False

async def test_supabase_connection():
    """Test Supabase connection"""
    print("\nTesting Supabase connection...")
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Supabase credentials not found")
        return False
    
    try:
        supabase = Client(supabase_url, supabase_key)
        
        # Test basic connection with a simple query
        result = supabase.table('documents').select('id').limit(1).execute()
        
        print("✅ Supabase connection successful")
        print(f"Found documents table with {len(result.data)} test records")
        return True
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {str(e)}")
        return False

async def test_embedding_connection():
    """Test embedding client connection"""
    print("\nTesting embedding client connection...")
    
    embedding_api_key = os.getenv('EMBEDDING_API_KEY', os.getenv('LLM_API_KEY'))
    embedding_base_url = os.getenv('EMBEDDING_BASE_URL', 'https://api.openai.com/v1')
    
    if not embedding_api_key or embedding_api_key == 'no-api-key-provided':
        print("❌ No valid embedding API key found")
        return False
    
    try:
        client = AsyncOpenAI(api_key=embedding_api_key, base_url=embedding_base_url)
        
        # Test embedding creation
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input="test embedding"
        )
        
        print("✅ Embedding API connection successful")
        print(f"Embedding dimension: {len(response.data[0].embedding)}")
        return True
        
    except Exception as e:
        print(f"❌ Embedding API connection failed: {str(e)}")
        return False

async def test_http_client():
    """Test basic HTTP client"""
    print("\nTesting HTTP client...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://httpbin.org/get", timeout=10.0)
            response.raise_for_status()
            
        print("✅ HTTP client working")
        return True
        
    except Exception as e:
        print(f"❌ HTTP client failed: {str(e)}")
        return False

async def main():
    """Run all connection tests"""
    print("🔍 Testing API connections and configuration...")
    print("=" * 50)
    
    # Test all connections
    results = []
    results.append(await test_openai_connection())
    results.append(await test_supabase_connection())
    results.append(await test_embedding_connection())
    results.append(await test_http_client())
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    if all(results):
        print("✅ All connections successful! System ready to run.")
    else:
        print("❌ Some connections failed. Check the errors above.")
        print("\n🔧 Troubleshooting tips:")
        if not results[0]:  # OpenAI failed
            print("- Verify your OpenAI API key is valid and has credits")
            print("- Check if the key has the right permissions")
        if not results[1]:  # Supabase failed
            print("- Verify Supabase URL and service key")
            print("- Check if the embeddings table exists")
        if not results[2]:  # Embedding failed
            print("- Check embedding API configuration")
        if not results[3]:  # HTTP failed
            print("- Check network connectivity")

if __name__ == "__main__":
    asyncio.run(main())