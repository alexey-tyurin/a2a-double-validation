# A2A Double Validation

A Python implementation of Google's Agent-to-Agent (A2A) Protocol with a multi-agent system for query processing with safety verification and critique.

## Architecture

This system uses four agents that work together:

1. **Manager Agent**: Coordinates the flow between agents
2. **Safeguard Agent**: Checks user queries for vulnerabilities using Meta's Guard-2 model
3. **Processor Agent**: Processes user queries using Gemma 3
4. **Critic Agent**: Evaluates responses for completeness and validity using Gemini 2.0 Flash

## Flow

1. User sends a query to the Manager Agent
2. Manager Agent sends user query to Safeguard Agent
3. Safeguard Agent checks query safety with Guard-2 and returns assessment
4. If the query is unsafe, Manager Agent rejects it
5. If safe, Manager Agent sends query to Processor Agent
6. Processor Agent processes query with Gemma 3 and returns result
7. Manager Agent sends the query and response to Critic Agent
8. Critic Agent evaluates response with Gemini 2.0 Flash
9. Manager Agent returns the processed response with evaluation to the user

## Setup

### Requirements

- Python 3.10+
- Google API Key for Gemini models
- Google Vertex AI project for Guard-2 model access

### Installation

1. Clone the repository
2. Create and activate a virtual environment:
   ```
   python -m venv a2a-env
   source a2a-env/bin/activate  # On Windows: a2a-env\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Copy `env.sample` to `.env` and fill in your API keys and project details:
   ```
   cp env.sample .env
   ```

## Running the System

Start the A2A system:

```
python main.py
```

This will start all four agents on separate ports:
- Manager Agent: http://localhost:8001
- Safeguard Agent: http://localhost:8002
- Processor Agent: http://localhost:8003
- Critic Agent: http://localhost:8004
- A2A Server: http://localhost:8000

## Usage

### Using the Client Utility

The project includes a client utility for interacting with the system:

#### Interactive Mode

```bash
python client.py
```

This opens an interactive session where you can type queries and see responses.

#### Single Query Mode

```bash
python client.py --query "What is the capital of France?"
```

### Using API Directly

Send a query to the Manager Agent's API endpoint:

```bash
curl -X POST http://localhost:8001/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the capital of France?"}'
```

The response will include both the answer and an evaluation of the response quality.

## License

[License](LICENSE)