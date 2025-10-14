"""
Command-line interface for the web search agent.

This module provides a simple command-line interface to interact with the web search agent.
"""

import asyncio
import os
import sys
from typing import Optional

from httpx import AsyncClient
from dotenv import load_dotenv

# Add the parent directory to sys.path to allow absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Use a relative import when running as a module
from agent import run_web_search_agent


async def main():
    """
    Run the command-line interface for the web search agent.
    """
    # Load environment variables
    load_dotenv(override=True)
    
    print("Web Search Agent CLI")
    print("--------------------")
    print("Type 'exit' or 'quit' to exit the program.")
    print("Type 'help' for help.")
    print()
    
    # Get the search provider information
    brave_api_key = os.getenv("BRAVE_API_KEY")
    searxng_base_url = os.getenv("SEARXNG_BASE_URL")
    
    if brave_api_key:
        print(f"Using Brave Search API for web searches")
    elif searxng_base_url:
        print(f"Using SearXNG at {searxng_base_url} for web searches")
    else:
        print("Warning: No search provider configured. Please set either BRAVE_API_KEY or SEARXNG_BASE_URL environment variable.")
    
    print()
    
    while True:
        try:
            # Get user input
            user_input = input("Enter your search query: ")
            
            # Check if the user wants to exit
            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break
                
            # Check if the user wants help
            if user_input.lower() == "help":
                print("\nHelp:")
                print("  - Enter a search query to search the web")
                print("  - Type 'exit' or 'quit' to exit the program")
                print("  - Type 'help' for this help message")
                print()
                continue
                
            # Run the agent
            print("\nSearching...")
            response = await run_web_search_agent(user_input)
            
            # Print the response
            print("\nResponse:")
            print(response)
            print()
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print()


if __name__ == "__main__":
    asyncio.run(main())
