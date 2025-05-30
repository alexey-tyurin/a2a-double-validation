#!/usr/bin/env python
# user_client.py - A2A Double Validation User Client
# This file was renamed from client.py to avoid conflicts with the common/client package

import argparse
import json
import sys
import requests
from typing import Dict, Any, Optional


def query_manager(query: str, host: str = "localhost", port: int = 9001) -> Optional[Dict[str, Any]]:
    """
    Send a query to the Manager Agent
    
    Args:
        query: The user query to send
        host: The host of the Manager Agent
        port: The port of the Manager Agent's FastAPI server (default: 9001)
            (A2A port + 1000)
        
    Returns:
        Dict: The response from the Manager Agent, or None if there was an error
    """
    url = f"http://{host}:{port}/api/query"
    headers = {"Content-Type": "application/json"}
    data = {"query": query}
    
    print(f"Connecting to: {url}")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an exception for 4XX/5XX responses
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        print(f"Response content: {e.response.content}")
        return None
    except Exception as e:
        print(f"Error querying Manager Agent: {str(e)}")
        return None


def check_system_status(host: str = "localhost", port: int = 8005) -> bool:
    """
    Check system status through the main API
    
    Args:
        host: The host of the main API
        port: The port of the main API (default: 8005)
        
    Returns:
        bool: True if the system is running, False otherwise
    """
    url = f"http://{host}:{port}/status"
    print(f"Checking system status at: {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        status_data = response.json()
        print("Status response:")
        print(json.dumps(status_data, indent=2))
        
        # Check if manager agent is running
        manager_status = status_data.get("agents", {}).get("manager", {}).get("status", "Unknown")
        if manager_status == "Running":
            return True
        else:
            print(f"Manager Agent status: {manager_status}")
            return False
    except Exception as e:
        print(f"Error checking system status: {str(e)}")
        return False


def main():
    """Main function for the client utility"""
    parser = argparse.ArgumentParser(description="A2A Double Validation Client")
    parser.add_argument("--query", "-q", type=str, help="Query to send to the system")
    parser.add_argument("--host", type=str, default="localhost", help="Host of the Manager Agent")
    parser.add_argument("--port", type=int, default=9001, help="Port of the Manager Agent's API (default: 9001)")
    parser.add_argument("--status", action="store_true", help="Check system status")
    
    args = parser.parse_args()
    
    # Check system status if requested
    if args.status:
        if check_system_status(args.host, 8005): # Always check status on main API port 8005
            print("System is running and Manager Agent is available!")
        else:
            print("System is not fully operational. Manager Agent may not be available.")
        return
    
    # If no query provided, enter interactive mode
    if not args.query:
        print("A2A Double Validation Client (Interactive Mode)")
        print("Type 'exit' or 'quit' to exit")
        print("-" * 50)
        
        while True:
            query = input("\nEnter your query: ")
            if query.lower() in ["exit", "quit"]:
                break
                
            response = query_manager(query, args.host, args.port)
            if response:
                print("\nResponse:")
                print("-" * 50)
                print(response.get("response", "No response"))
                print("-" * 50)
    else:
        # Single query mode
        response = query_manager(args.query, args.host, args.port)
        if response:
            print(response.get("response", "No response"))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0) 