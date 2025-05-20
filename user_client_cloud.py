#!/usr/bin/env python
# user_client_cloud.py - A2A Double Validation Cloud Client

import argparse
import json
import sys
import requests
from typing import Dict, Any, Optional
import os

# Try to import cloud configuration
try:
    from cloud_config import MANAGER_URL
except ImportError:
    print("Cloud configuration not found. Please run deploy_to_cloud_run.sh first.")
    MANAGER_URL = os.environ.get("MANAGER_URL", "")
    if not MANAGER_URL:
        print("Error: MANAGER_URL not found in environment variables.")
        print("Please set MANAGER_URL or run deploy_to_cloud_run.sh to generate cloud_config.py")
        sys.exit(1)


def query_manager(query: str, manager_url: str = MANAGER_URL) -> Optional[Dict[str, Any]]:
    """
    Send a query to the Manager Agent in the cloud
    
    Args:
        query: The user query to send
        manager_url: The URL of the Manager Agent API (from cloud_config.py)
        
    Returns:
        Dict: The response from the Manager Agent, or None if there was an error
    """
    url = manager_url
    headers = {"Content-Type": "application/json"}
    data = {"query": query}
    
    print(f"Connecting to cloud service: {url}")
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()  # Raise an exception for 4XX/5XX responses
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        print(f"Response content: {e.response.content}")
        return None
    except Exception as e:
        print(f"Error querying Manager Agent: {str(e)}")
        return None


def main():
    """Main function for the cloud client utility"""
    parser = argparse.ArgumentParser(description="A2A Double Validation Cloud Client")
    parser.add_argument("--query", "-q", type=str, help="Query to send to the system")
    parser.add_argument("--url", type=str, default=MANAGER_URL, 
                       help=f"URL of the Manager Agent's API (default: {MANAGER_URL})")
    
    args = parser.parse_args()
    
    # If no query provided, enter interactive mode
    if not args.query:
        print("A2A Double Validation Cloud Client (Interactive Mode)")
        print("Type 'exit' or 'quit' to exit")
        print("-" * 50)
        print(f"Connected to: {args.url}")
        print("-" * 50)
        
        while True:
            query = input("\nEnter your query: ")
            if query.lower() in ["exit", "quit"]:
                break
                
            response = query_manager(query, args.url)
            if response:
                print("\nResponse:")
                print("-" * 50)
                
                # Extract just the actual response part (before the evaluation)
                full_response = response.get("response", "No response")
                if "---" in full_response:
                    parts = full_response.split("---")
                    print(parts[0].strip())
                    print("-" * 50)
                    print("Evaluation:")
                    print(parts[1].strip())
                else:
                    print(full_response)
                
                print("-" * 50)
    else:
        # Single query mode
        response = query_manager(args.query, args.url)
        if response:
            # Extract just the actual response part (before the evaluation)
            full_response = response.get("response", "No response")
            if "---" in full_response:
                parts = full_response.split("---")
                print(parts[0].strip())
            else:
                print(full_response)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0) 