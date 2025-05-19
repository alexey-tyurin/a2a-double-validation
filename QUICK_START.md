# Quick Start Guide for A2A Double Validation

This guide will help you quickly set up and run the A2A Double Validation system.

## Prerequisites

Ensure you have:
- Python 3.10+
- Google API Key (for Gemini models)
- HuggingFace Token (for Prompt Guard 2 model)

## Setup Instructions

1. **Create a fresh virtual environment:**
   ```bash
   python -m venv fresh_env
   source fresh_env/bin/activate  # On Windows: fresh_env\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   
   > Note: The project uses some dependencies for server-sent events (SSE):
   > - `httpx-sse` for client SSE connections
   > - `sse-starlette` for server SSE responses
   >
   > If you encounter "ModuleNotFoundError" errors, run:
   > ```bash
   > pip install httpx-sse sse-starlette
   > ```
   >
   > This project requires NumPy 1.x (not 2.x) for compatibility with PyTorch.
   > If you encounter NumPy-related errors, downgrade NumPy:
   > ```bash
   > pip install numpy==1.26.4
   > ```

3. **Set up environment variables:**
   ```bash
   cp env.sample .env
   ```
   
   Open the `.env` file and fill in:
   - `GOOGLE_API_KEY`: Your Google API key for Gemini models
   - `HUGGINGFACE_TOKEN`: Your HuggingFace token for accessing Prompt Guard 2 model
   - `VERTEX_AI_PROJECT`: Your Google Cloud project ID (if using Vertex AI)
   - `VERTEX_AI_LOCATION`: Your Google Cloud region (default: us-central1)

## Running the System

### Start the complete system:
```bash
python main.py
```

### To use the system:
```bash
# Interactive mode
python user_client.py

# Single query mode
python user_client.py --query "What is the capital of France?"

# Check system status
python user_client.py --status
```

## What's Happening Behind the Scenes

When you run `main.py`, the system:

1. **Initializes four specialized AI agents:**
   - Manager Agent: Coordinates the overall process flow
   - Safeguard Agent: Checks queries for safety using Meta's Prompt Guard 2 model
   - Processor Agent: Processes safe queries using Gemini 1.5 Pro
   - Critic Agent: Evaluates responses using Gemini 1.5 Flash

2. **Sets up communication:**
   - Agents communicate using Google's Agent-to-Agent (A2A) Protocol
   - The system exposes external API endpoints for user interaction

3. **Processes user queries:**
   - User queries are checked for safety
   - Safe queries are processed to generate responses
   - Responses are evaluated for quality and completeness
   - Final results are returned to the user

## Troubleshooting

If you encounter issues:

1. **Check API keys:**
   - Ensure your `GOOGLE_API_KEY` and `HUGGINGFACE_TOKEN` are valid

2. **Check model access:**
   - Verify your account has access to Prompt Guard 2 model on HuggingFace
   - Ensure you have proper permissions for Google Gemini models

3. **Check ports:**
   - Ensure ports 8001-8004 and 9001-9004 are available on your system

4. **Check logs:**
   - Monitor the terminal output for error messages 