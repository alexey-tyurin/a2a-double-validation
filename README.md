# A2A Double Validation

Multi-agent system for query processing with safety verification and critique 
  built with Google A2A protocol, Google ADK, Llama Prompt Guard 2, Gemma 3 and Gemini 2.0 Flash.

## Architecture

```mermaid
graph TD
    User[User/Client] <-->|Query/Response| Manager[Manager Agent]
    
    subgraph "A2A Protocol Communication"
        Manager <-->|Step 1: Check Query Safety| Safeguard[Safeguard Agent]
        Manager <-->|Step 2: Process Query| Processor[Processor Agent]
        Manager <-->|Step 3: Evaluate Response| Critic[Critic Agent]
    end
    
    Safeguard -->|Uses| Guard[Llama Prompt Guard 2]
    Processor -->|Uses| Gemma[Gemma 3 Model]
    Critic -->|Uses| Gemini[Gemini 2.0 Flash]
    
    classDef models fill:#f9f,stroke:#333,stroke-width:2px
    classDef agents fill:#bbf,stroke:#333,stroke-width:2px
    classDef external fill:#fff,stroke:#333,stroke-width:2px
    
    class Guard,Gemma,Gemini models
    class Manager,Safeguard,Processor,Critic agents
    class User external
    
    %% Flow description
    linkStyle 0 stroke:#000,stroke-width:2px
    linkStyle 1 stroke:#f00,stroke-width:2px
    linkStyle 2 stroke:#0a0,stroke-width:2px
    linkStyle 3 stroke:#00f,stroke-width:2px
```

This system uses four agents that work together:

1. **Manager Agent**: Coordinates the flow between agents
2. **Safeguard Agent**: Checks user queries for vulnerabilities using Meta's Prompt Guard 2 model
3. **Processor Agent**: Processes user queries using Gemma 3
4. **Critic Agent**: Evaluates responses for completeness and validity using Gemini 2.0 Flash

Each agent communicates using the Google Agent-to-Agent (A2A) Protocol for inter-agent communication, with FastAPI handling only external user-facing APIs.

## Project Structure

The project is organized by agent, with each agent in its own module:

- **agent_manager/**: Manager Agent implementation
- **agent_processor/**: Processor Agent implementation
- **agent_critic/**: Critic Agent implementation
- **agent_safeguard/**: Safeguard Agent implementation
- **models/**: AI model integrations (Gemini, Gemma, Guard)
- **config/**: Configuration settings
- **utils/**: Utility functions
- **common/**: Common types and A2A protocol implementation

Each agent folder contains:
- **__init__.py**: Module exports
- **__main__.py**: Entry point for running the agent individually
- **task_manager.py**: Agent-specific task management
- **[agent_name].py**: Agent implementation

## Flow

1. User sends a query to the Manager Agent
2. Manager Agent sends user query to Safeguard Agent via A2A
3. Safeguard Agent checks query safety with Prompt Guard 2 and returns assessment via A2A
4. If the query is unsafe, Manager Agent rejects it
5. If safe, Manager Agent sends query to Processor Agent via A2A
6. Processor Agent processes query with Gemma 3 and returns result via A2A
7. Manager Agent sends the query and response to Critic Agent via A2A
8. Critic Agent evaluates response with Gemini 2.0 Flash and returns via A2A
9. Manager Agent returns the processed response with evaluation to the user

## Setup

### Requirements

- Python 3.10+
- Google API Key for Gemini and Gemma models
- Google Vertex AI project for Vertex AI models
- HuggingFace API Token for Prompt Guard 2 model

> **Important Note about Llama Prompt Guard 2**: To use the Llama Prompt Guard 2 model, you must:
> 1. Fill out the "LLAMA 4 COMMUNITY LICENSE AGREEMENT" at [https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-86M](https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-86M)
> 2. Get your request to access this repository approved by Meta
> 3. Only after approval will you be able to download and use this model in the project

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/alexey-tyurin/a2a-double-validation.git
   cd a2a-double-validation
   ```

2. Create and activate a fresh virtual environment:
   ```
   python -m venv fresh_env
   source fresh_env/bin/activate  # On Windows: fresh_env\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
   
   > **Note**: This project requires NumPy 1.x (not 2.x) for compatibility with PyTorch.
   > If you encounter NumPy-related errors, downgrade NumPy:
   > ```bash
   > pip install numpy==1.26.4
   > ```
   >
   > The Prompt Guard 2 model requires accelerate for efficient loading:
   > ```bash
   > pip install accelerate
   > ```

4. Copy `env.sample` to `.env` and fill in your API keys and project details:
   ```
   cp env.sample .env
   ```
   Be sure to add your HuggingFace token for Prompt Guard 2 model access.

> **Note for Python 3.10 Users**: If you're using Python 3.10, you need to apply a compatibility patch after installation:
> ```bash
> python python310_compatibility_patch.py
> ```
> This patch updates the typing imports to work with Python 3.10. Python 3.11+ users don't need this step.

## Running the System

### Running All Agents

You can start all agents at once using either:

```bash
python run_all.py
```

or

```bash
python main.py
```

### Process Management

The repository includes utility scripts to help you manage running processes:

```bash
# Check if all processes are running
./check_processes.sh

# Stop all running processes
./kill_processes.sh
```

The `check_processes.sh` script will verify:
- If the main Python process is running
- If all A2A servers are listening on their expected ports
- The count of running agent processes

The `kill_processes.sh` script will:
- Gracefully terminate all processes related to the application
- Force kill any processes that don't respond to graceful termination
- Clear any processes bound to the application's ports

### Running Individual Agents

You can also run agents individually, which is useful for development or debugging:

```bash
# Start the Manager Agent
python -m agent_manager

# Start the Processor Agent
python -m agent_processor

# Start the Critic Agent
python -m agent_critic

# Start the Safeguard Agent
python -m agent_safeguard
```

The agents will be available on the following ports:

- **A2A Communication Ports**:
  - Manager Agent: http://localhost:8001
  - Safeguard Agent: http://localhost:8002
  - Processor Agent: http://localhost:8003
  - Critic Agent: http://localhost:8004

- **External API Ports** (A2A port + 1000):
  - Manager Agent API: http://localhost:9001
  - Safeguard Agent API: http://localhost:9002
  - Processor Agent API: http://localhost:9003
  - Critic Agent API: http://localhost:9004

## Usage

### Using the Client Utility

The project includes a client utility for interacting with the system:

#### Interactive Mode

```bash
python user_client.py
```

This opens an interactive session where you can type queries and see responses.

#### Single Query Mode

```bash
python user_client.py --query "What is the capital of France?"
```

#### Check System Status

```bash
python user_client.py --status
```

### Running Test Scenarios

The project includes a test script for evaluating the system's performance with both benign queries and prompt injection attacks:

```bash
python test_a2a_scenarios.py
```

This will run 10 benign test queries and 10 prompt injection tests, and provide a summary of the results.

#### Test Options

```bash
# Save test results to a JSON file
python test_a2a_scenarios.py --output results.json

# Test against a different host or port
python test_a2a_scenarios.py --host your-host.com --port 9001
```

The test script will:
- Process 20 predefined test queries (10 benign, 10 prompt injections)
- Parse each response into its components (answer, evaluation, explanation)
- Track which injection attempts were blocked by the system
- Provide a summary of test results
- Optionally save detailed results to a JSON file

### Using API Directly

Send a query to the Manager Agent's API endpoint:

```bash
curl -X POST http://localhost:9001/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the capital of France?"}'
```

The response will include both the answer and an evaluation of the response quality.

## Cloud Deployment

The A2A Double Validation system can be deployed to **Google Cloud Platform (Vertex AI)** for scalable, serverless operation using Cloud Run and Vertex AI services.

### Prerequisites

- Google Cloud Platform account with billing enabled
- Access to Google Vertex AI services
- gcloud CLI installed and configured
- Docker installed locally (for local development) or access to Cloud Shell

### Google Cloud Setup

#### 1. Setup Cloud Project in Cloud Shell Terminal

1. **Access Google Cloud Console**: Go to [https://console.cloud.google.com](https://console.cloud.google.com)

2. **Open Cloud Shell**: Click the Cloud Shell icon (terminal icon) in the top right corner of the Google Cloud Console

3. **Authenticate with Google Cloud**:
   ```bash
   # Authenticate with your Google Cloud account
   gcloud auth login
   
   # Verify authentication
   gcloud auth list
   ```

4. **Create or select a project**:
   ```bash
   # Create a new project (replace PROJECT_ID with your desired project ID)
   gcloud projects create PROJECT_ID --name="A2A Double Validation"
   
   # Or list existing projects
   gcloud projects list
   
   # Set the active project
   gcloud config set project PROJECT_ID
   ```

5. **Enable required APIs**:
   ```bash
   # Enable necessary Google Cloud APIs
   gcloud services enable run.googleapis.com
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable containerregistry.googleapis.com
   gcloud services enable secretmanager.googleapis.com
   gcloud services enable aiplatform.googleapis.com
   gcloud services enable compute.googleapis.com
   gcloud services enable logging.googleapis.com
   gcloud services enable cloudresourcemanager.googleapis.com
   ```

#### 2. Setup Vertex AI Permissions

Grant your account the necessary permissions for Vertex AI and related services:

```bash
# Get your current account email
ACCOUNT_EMAIL=$(gcloud config get-value account)

# Grant Vertex AI permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="user:$ACCOUNT_EMAIL" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="user:$ACCOUNT_EMAIL" \
    --role="roles/aiplatform.serviceAgent"

# Grant Cloud Run permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="user:$ACCOUNT_EMAIL" \
    --role="roles/run.admin"

# Grant Secret Manager permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="user:$ACCOUNT_EMAIL" \
    --role="roles/secretmanager.admin"

# Grant Compute Engine permissions (for VM creation)
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="user:$ACCOUNT_EMAIL" \
    --role="roles/compute.admin"

# Grant necessary service account permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="user:$ACCOUNT_EMAIL" \
    --role="roles/iam.serviceAccountAdmin"
```

#### 3. Create and Setup VM Instance

Cloud Shell will not work for this project as Cloud Shell is limited to 5GB of disk space.
This project needs more than 30GB of disk space to build docker images, get all dependencies and 
  download Llama Prompt Guard 2 model locally. So you need to use a dedicated VM instead of Cloud Shell.

```bash
# Create Ubuntu VM with necessary permissions and scopes
gcloud compute instances create "py310-vm" \
    --machine-type="e2-standard-2" \
    --image-family="ubuntu-2204-lts" \
    --image-project="ubuntu-os-cloud" \
    --boot-disk-size="50GB" \
    --zone="us-central1-a" \
    --scopes="https://www.googleapis.com/auth/cloud-platform" \
    --service-account="$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')-compute@developer.gserviceaccount.com" \
    --tags="a2a-vm"

# Create firewall rule for the VM (if needed for external access)
gcloud compute firewall-rules create allow-a2a-vm \
    --allow tcp:22,tcp:8001-8005,tcp:9001-9005 \
    --source-ranges 0.0.0.0/0 \
    --target-tags a2a-vm \
    --description "Allow SSH and A2A ports for A2A Double Validation VM"
```

#### 4. Connect to VM

```bash
# Connect to the VM via SSH
gcloud compute ssh py310-vm --zone=us-central1-a
```

#### 5. Clone Repository

```bash
# Clone the A2A Double Validation repository
git clone https://github.com/alexey-tyurin/a2a-double-validation.git
cd a2a-double-validation
```

### Deployment Steps

1. Copy `env.sample` to `.env` and fill in your API keys and project details:
   ```bash
   cp env.sample .env
   ```
   Be sure to add your HuggingFace token for Prompt Guard 2 model access.

2. Authenticate with Google Cloud:
   ```bash
   gcloud auth login
   ```
   This ensures you have the necessary permissions to create secrets and grant access to service accounts.

3. Set up Google Cloud Secret Manager for sensitive credentials:
   ```bash
   ./setup_secrets.sh --project your-gcp-project-id
   ```
   
   This script will:
   - Read `GOOGLE_API_KEY` and `HUGGINGFACE_TOKEN` from your `.env` file
   - Create secrets in Google Cloud Secret Manager
   - Grant access permissions to the default compute service account
   - Enable the Secret Manager API if needed

4. Run setup script:
   ```bash
   ./setup_cloud.sh
   ```
   
   This script will:
   - Install Python 3.10+ if not already installed
   - Install Docker and Docker Compose if not already installed
   - Install Google Cloud CLI if not already installed
   - Create a Python virtual environment
   - Install all dependencies from requirements.txt
   - Apply Python 3.10 compatibility patch if needed
   - Start the application
   - Download Llama Prompt Guard 2 model in local cache, so it can be used in creating Docker image for safeguard
   
   > **Note**: After Docker installation, you may need to log out and back in for group permissions to take effect. If you plan to use Cloud Run deployment, run `gcloud auth login` after the script completes.

   **Docker Permissions Fix**: If you encounter a Docker permissions error like "permission denied while trying to connect to the Docker daemon socket", run:
   ```bash
   ./fix_docker_permissions.sh
   ```
   Then either log out/in, use `newgrp docker`, or try the deployment again.

5. Run script to check if all processes are running
   ```bash
   ./check_processes.sh
   ```

6. Optionally - run client:
```bash
python user_client.py
```

7. Stop all running processes
```bash
./kill_processes.sh
```

8. Deploy all agents to Cloud Run:
   ```bash
   ./deploy_to_cloud_run.sh --project your-gcp-project-id
   ```
   
   This script will:
   - Read non-sensitive environment variables from your `.env` file (`VERTEX_AI_PROJECT`, `VERTEX_AI_LOCATION`)
   - Validate that all required variables are set
   - Check that required secrets exist in Secret Manager
   - Build Docker images for each agent
   - For safeguard Docker image it uses Llama Prompt Guard 2 model downloaded to local cache in previous step.
     This way safeguard instance will not download Llama Prompt Guard 2 model, and instead use it from its image.
     This will improve latency.
   - Push them to Google Container Registry
   - Deploy them as Cloud Run services with:
     - Environment variables set via `--set-env-vars` (non-sensitive data)
     - Secrets mounted via `--set-secrets` (sensitive credentials)
   - Generate a `cloud_config.py` file with service URLs
   
   > **Security Note**: Sensitive credentials (`GOOGLE_API_KEY`, `HUGGINGFACE_TOKEN`) are stored securely in Google Cloud Secret Manager and mounted as environment variables at runtime. They are never embedded in container images or visible in deployment configurations.

### Cloud Service Management

Once your services are deployed, you can use the included management scripts to monitor and control them:

#### Check Cloud Services Status

```bash
# Check status of all A2A Cloud Run services
./check_cloud_status.sh --project your-gcp-project-id

# Check services in a different region
./check_cloud_status.sh --project your-gcp-project-id --region us-central1
```

The status check script will:
- List all A2A Cloud Run services and their status
- Show detailed information for each service (URL, status, latest revision)
- Test endpoint connectivity for each service
- Provide a summary of service URLs for easy access
- Give helpful tips for troubleshooting

#### Stop/Delete Cloud Services

```bash
# Delete all A2A Cloud Run services (with confirmation)
./kill_cloud_services.sh --project your-gcp-project-id

# Force deletion without confirmation prompt
./kill_cloud_services.sh --project your-gcp-project-id --force

# Delete services in a different region
./kill_cloud_services.sh --project your-gcp-project-id --region us-central1
```

The deletion script will:
- Check which A2A services exist before deletion
- Show a summary of services to be deleted
- Prompt for confirmation (unless `--force` is used)
- Delete all A2A Cloud Run services
- Clean up temporary deployment files (`url_*.txt`, `cloud_config.py`)
- Provide a summary of the deletion operation

> **Note**: Deleting Cloud Run services is permanent and cannot be undone. The services will need to be redeployed using the deployment script.

### Cloud Client

Once deployed, you can interact with the cloud-deployed system using the cloud client:

```bash
python user_client_cloud.py
```

The cloud client works similarly to the local client but connects to the Cloud Run endpoints automatically.

### Cloud Testing

You can also run test scenarios against the cloud deployment:

```bash
python test_a2a_scenarios_cloud.py
```

This will run the same test scenarios as the local test script but against the cloud deployment.

## Cleanup Google Cloud Resources

When you're done with the project, you can clean up all created resources to avoid ongoing charges:

### 1. Delete Cloud Run Services

```bash
# Delete all A2A Cloud Run services
./kill_cloud_services.sh --project your-gcp-project-id --force
```

### 2. Delete VM Instance

```bash
# Delete the VM instance
gcloud compute instances delete py310-vm --zone=us-central1-a --quiet

# Delete the firewall rule
gcloud compute firewall-rules delete allow-a2a-vm --quiet
```

### 3. Delete Secrets from Secret Manager

```bash
# Delete secrets
gcloud secrets delete google-api-key --quiet
gcloud secrets delete huggingface-token --quiet
```

### 4. Clean up Container Images

```bash
# List and delete container images from Container Registry
gcloud container images list --repository=gcr.io/your-gcp-project-id

# Delete specific images (replace with actual image names)
gcloud container images delete gcr.io/your-gcp-project-id/a2a-manager-agent --force-delete-tags --quiet
gcloud container images delete gcr.io/your-gcp-project-id/a2a-safeguard-agent --force-delete-tags --quiet
gcloud container images delete gcr.io/your-gcp-project-id/a2a-processor-agent --force-delete-tags --quiet
gcloud container images delete gcr.io/your-gcp-project-id/a2a-critic-agent --force-delete-tags --quiet
```

### 5. Remove IAM Policy Bindings (Optional)

```bash
# Get your account email
ACCOUNT_EMAIL=$(gcloud config get-value account)
PROJECT_ID=$(gcloud config get-value project)

# Remove Vertex AI permissions
gcloud projects remove-iam-policy-binding $PROJECT_ID \
    --member="user:$ACCOUNT_EMAIL" \
    --role="roles/aiplatform.user"

gcloud projects remove-iam-policy-binding $PROJECT_ID \
    --member="user:$ACCOUNT_EMAIL" \
    --role="roles/aiplatform.serviceAgent"

# Remove other permissions (only if you don't need them for other projects)
gcloud projects remove-iam-policy-binding $PROJECT_ID \
    --member="user:$ACCOUNT_EMAIL" \
    --role="roles/run.admin"

gcloud projects remove-iam-policy-binding $PROJECT_ID \
    --member="user:$ACCOUNT_EMAIL" \
    --role="roles/secretmanager.admin"

gcloud projects remove-iam-policy-binding $PROJECT_ID \
    --member="user:$ACCOUNT_EMAIL" \
    --role="roles/compute.admin"

gcloud projects remove-iam-policy-binding $PROJECT_ID \
    --member="user:$ACCOUNT_EMAIL" \
    --role="roles/iam.serviceAccountAdmin"
```

### 6. Delete the Entire Project (Nuclear Option)

If you created a dedicated project for this A2A system and want to remove everything:

```bash
# ⚠️ WARNING: This will delete the ENTIRE project and ALL resources in it
# Make sure this project only contains A2A resources
gcloud projects delete your-gcp-project-id
```

> **Important**: Deleting the project will remove ALL resources, billing data, and access permissions. This action cannot be undone.

### 7. Verify Cleanup

Check that all resources have been removed:

```bash
# Check Cloud Run services
gcloud run services list --region=us-central1

# Check VM instances
gcloud compute instances list

# Check secrets
gcloud secrets list

# Check container images
gcloud container images list --repository=gcr.io/your-gcp-project-id
```

## 🙏 Acknowledgements

This project relies on several advanced AI and communication technologies:

- **Google Agent-to-Agent (A2A) Protocol**: For standardized inter-agent communication
- **Google Agent Development Kit (ADK)**: For agent infrastructure components
- **Meta's Llama Prompt Guard 2**: For safe query validation and prompt injection protection
- **Google Gemma 3**: For efficient user query processing
- **Google Gemini 2.0 Flash**: For rapid response evaluation and criticism

Thanks to all the teams developing these cutting-edge technologies that make advanced multi-agent systems possible.

## Contact Information

For any questions or feedback, please contact Alexey Tyurin at altyurin3@gmail.com.

## License

This project uses MIT license: [License](LICENSE)