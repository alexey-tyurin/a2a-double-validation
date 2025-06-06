#!/bin/bash
# Script to deploy all agents to Google Cloud Run

# Exit immediately if a command exits with a non-zero status
set -e

# Default values
PROJECT_ID=""
REGION="us-central1"
ENV_FILE=".env"
SKIP_CLEANUP=false

# Function to show usage
function show_usage {
  echo "Usage: $0 [options]"
  echo "Options:"
  echo "  -p, --project     Google Cloud Project ID (required)"
  echo "  -r, --region      Google Cloud Region (default: us-central1)"
  echo "  -e, --env-file    Environment file to use (default: .env)"
  echo "  --skip-cleanup    Skip Docker cleanup to preserve images"
  echo "  -h, --help        Show this help message"
  echo ""
  echo "Prerequisites:"
  echo "  1. Create secrets in Secret Manager:"
  echo "     gcloud secrets create google-api-key --replication-policy=\"automatic\""
  echo "     echo -n \"your_actual_google_api_key\" | gcloud secrets versions add google-api-key --data-file=-"
  echo "     gcloud secrets create huggingface-token --replication-policy=\"automatic\""
  echo "     echo -n \"your_actual_huggingface_token\" | gcloud secrets versions add huggingface-token --data-file=-"
  echo ""
  echo "  2. Grant permissions to the default compute service account:"
  echo "     PROJECT_NUMBER=\$(gcloud projects describe YOUR_PROJECT_ID --format='value(projectNumber)')"
  echo "     SERVICE_ACCOUNT=\"\${PROJECT_NUMBER}-compute@developer.gserviceaccount.com\""
  echo "     gcloud secrets add-iam-policy-binding google-api-key --member=\"serviceAccount:\${SERVICE_ACCOUNT}\" --role=\"roles/secretmanager.secretAccessor\""
  echo "     gcloud secrets add-iam-policy-binding huggingface-token --member=\"serviceAccount:\${SERVICE_ACCOUNT}\" --role=\"roles/secretmanager.secretAccessor\""
  exit 1
}

# Function to cleanup Docker images and free disk space
function cleanup_docker {
  echo "===================================================="
  echo "Cleaning up Docker images to free disk space..."
  echo "===================================================="
  
  # Remove dangling images (untagged images)
  echo "Removing dangling images..."
  docker image prune -f || true
  
  # Remove images older than 2 hours that are not currently used
  echo "Removing images older than 2 hours..."
  docker image prune -a -f --filter "until=2h" || true
  
  # Remove old images for this project specifically (keep the latest)
  echo "Removing old project images (keeping latest)..."
  for service in "a2a-manager-agent" "a2a-safeguard-agent" "a2a-processor-agent" "a2a-critic-agent"; do
    # Get all images for this service, sorted by creation date (newest first)
    old_images=$(docker images "gcr.io/$PROJECT_ID/$service" --format "{{.ID}}" | tail -n +2)
    if [ ! -z "$old_images" ]; then
      echo "Removing old images for $service..."
      echo "$old_images" | while read image_id; do
        if [ ! -z "$image_id" ]; then
          echo "  Removing image: $image_id"
          docker rmi "$image_id" -f 2>/dev/null || true
        fi
      done
    fi
  done
  
  # Clean up build cache older than 2 hours
  echo "Cleaning up Docker build cache older than 2 hours..."
  docker builder prune -f --filter "until=2h" || true
  
  # Remove unused volumes
  echo "Removing unused Docker volumes..."
  docker volume prune -f || true
  
  # Show disk usage after cleanup
  echo "Docker disk usage after cleanup:"
  docker system df || true
  
  echo "Docker cleanup completed."
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -p|--project)
      PROJECT_ID="$2"
      shift
      shift
      ;;
    -r|--region)
      REGION="$2"
      shift
      shift
      ;;
    -e|--env-file)
      ENV_FILE="$2"
      shift
      shift
      ;;
    --skip-cleanup)
      SKIP_CLEANUP=true
      shift
      ;;
    -h|--help)
      show_usage
      ;;
    *)
      echo "Unknown option: $1"
      show_usage
      ;;
  esac
done

# Check if required arguments are provided
if [[ -z "$PROJECT_ID" ]]; then
  echo "Error: Google Cloud Project ID is required"
  show_usage
fi

# Check if env file exists
if [[ ! -f "$ENV_FILE" ]]; then
  echo "Environment file $ENV_FILE not found. Creating from env.sample..."
  cp env.sample "$ENV_FILE"
  echo "Please edit $ENV_FILE with your actual API keys and credentials before continuing."
  exit 1
fi

# Function to read and validate environment variables
function load_env_vars {
  echo "Loading environment variables from $ENV_FILE..."
  
  # Source the env file to load variables
  set -a  # automatically export all variables
  source "$ENV_FILE"
  set +a  # stop automatically exporting
  
  # Validate required environment variables
  required_vars=("VERTEX_AI_PROJECT" "VERTEX_AI_LOCATION")
  missing_vars=()
  
  for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
      missing_vars+=("$var")
    fi
  done
  
  if [[ ${#missing_vars[@]} -gt 0 ]]; then
    echo "Error: Missing required environment variables in $ENV_FILE:"
    printf '  %s\n' "${missing_vars[@]}"
    echo "Please set these variables in $ENV_FILE before deploying."
    exit 1
  fi
  
  echo "All required environment variables are set."
  echo "Note: GOOGLE_API_KEY and HUGGINGFACE_TOKEN will be loaded from Secret Manager"
}

# Function to check if secrets exist
function check_secrets {
  echo "Checking if required secrets exist in Secret Manager..."
  
  local secrets_missing=false
  
  # Check google-api-key secret
  if ! gcloud secrets describe google-api-key --project="$PROJECT_ID" >/dev/null 2>&1; then
    echo "Error: Secret 'google-api-key' not found in Secret Manager"
    secrets_missing=true
  else
    echo "✓ Secret 'google-api-key' found"
  fi
  
  # Check huggingface-token secret
  if ! gcloud secrets describe huggingface-token --project="$PROJECT_ID" >/dev/null 2>&1; then
    echo "Error: Secret 'huggingface-token' not found in Secret Manager"
    secrets_missing=true
  else
    echo "✓ Secret 'huggingface-token' found"
  fi
  
  if [ "$secrets_missing" = true ]; then
    echo ""
    echo "Please create the missing secrets using the commands shown in --help"
    exit 1
  fi
}

# Load and validate environment variables
load_env_vars

# Check if secrets exist
check_secrets

# Confirm deployment
echo "This script will deploy 4 agents to Google Cloud Run in project: $PROJECT_ID"
echo "Region: $REGION"
echo "Environment file: $ENV_FILE"
echo "Sensitive credentials will be loaded from Secret Manager"
echo "Non-sensitive environment variables will be set directly"
if [ "$SKIP_CLEANUP" = false ]; then
  echo "Docker cleanup: ENABLED (will remove old images to free disk space)"
else
  echo "Docker cleanup: DISABLED (images will be preserved)"
fi
read -p "Do you want to continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Deployment canceled"
  exit 1
fi

# Ensure gcloud is configured with the right project
echo "Setting Google Cloud project to $PROJECT_ID"
gcloud config set project "$PROJECT_ID"

# Initial cleanup to start with a clean slate
echo "===================================================="
echo "Initial Docker cleanup before deployment..."
echo "===================================================="
echo "Docker disk usage before cleanup:"
docker system df || true
if [ "$SKIP_CLEANUP" = false ]; then
  cleanup_docker
fi

# Function to deploy an agent
function deploy_agent {
  local agent_name="$1"
  local dockerfile="$2"
  local port="$3"
  local memory="$4"
  local cpu="$5"
  local service_name="a2a-$agent_name-agent"
  local image_name="gcr.io/$PROJECT_ID/$service_name"
  
  echo "===================================================="
  echo "Deploying $agent_name Agent to Cloud Run"
  echo "===================================================="
  
  # Build container image
  echo "Building Docker image: $image_name"
  docker build -t "$image_name" -f "$dockerfile" .
  
  # Push to Google Container Registry
  echo "Pushing image to Google Container Registry"
  docker push "$image_name"
  
  # Set environment variables and secrets for Cloud Run
  echo "Setting environment variables and secrets for Cloud Run deployment..."
  
  # For manager agent, we need to set agent URLs after all services are deployed
  # For now, deploy with basic environment variables
  if [[ "$agent_name" == "manager" ]]; then
    # Deploy manager agent with PORT environment variable for Cloud Run
    echo "Deploying service to Cloud Run"
    gcloud run deploy "$service_name" \
      --image "$image_name" \
      --platform managed \
      --region "$REGION" \
      --port "$port" \
      --memory "$memory" \
      --cpu "$cpu" \
      --allow-unauthenticated \
      --min-instances 1 \
      --max-instances 1 \
      --timeout 300 \
      --set-env-vars="DEPLOYMENT_ENV=cloud,HOST=0.0.0.0,VERTEX_AI_PROJECT=$VERTEX_AI_PROJECT,VERTEX_AI_LOCATION=$VERTEX_AI_LOCATION" \
      --set-secrets="GOOGLE_API_KEY=google-api-key:latest,HUGGINGFACE_TOKEN=huggingface-token:latest"
  else
    # Deploy other agents normally (they only run A2A servers)
    echo "Deploying service to Cloud Run"
    gcloud run deploy "$service_name" \
      --image "$image_name" \
      --platform managed \
      --region "$REGION" \
      --port "$port" \
      --memory "$memory" \
      --cpu "$cpu" \
      --allow-unauthenticated \
      --min-instances 1 \
      --max-instances 1 \
      --timeout 300 \
      --set-env-vars="DEPLOYMENT_ENV=cloud,HOST=0.0.0.0,VERTEX_AI_PROJECT=$VERTEX_AI_PROJECT,VERTEX_AI_LOCATION=$VERTEX_AI_LOCATION" \
      --set-secrets="GOOGLE_API_KEY=google-api-key:latest,HUGGINGFACE_TOKEN=huggingface-token:latest"
  fi
  
  # Get the service URL
  service_url=$(gcloud run services describe "$service_name" --platform managed --region "$REGION" --format='value(status.url)')
  echo "$agent_name Agent deployed at: $service_url"
  echo "$service_url" > "url_$agent_name.txt"
}

# Deploy each agent
deploy_agent "safeguard" "Dockerfile.safeguard" 8002 "2Gi" "2"
deploy_agent "processor" "Dockerfile.processor" 8003 "2Gi" "2"
deploy_agent "critic" "Dockerfile.critic" 8004 "1Gi" "1"

# Deploy manager agent last and update it with agent URLs
deploy_agent "manager" "Dockerfile.manager" 9001 "1Gi" "1"

echo "===================================================="
echo "Updating Manager Agent with service URLs..."
echo "===================================================="

# Update manager agent with agent URLs
SAFEGUARD_URL=$(cat url_safeguard.txt)
PROCESSOR_URL=$(cat url_processor.txt)
CRITIC_URL=$(cat url_critic.txt)

# Redeploy manager agent with agent URLs
gcloud run services update a2a-manager-agent \
  --platform managed \
  --region "$REGION" \
  --set-env-vars="DEPLOYMENT_ENV=cloud,HOST=0.0.0.0,VERTEX_AI_PROJECT=$VERTEX_AI_PROJECT,VERTEX_AI_LOCATION=$VERTEX_AI_LOCATION,SAFEGUARD_URL=$SAFEGUARD_URL,PROCESSOR_URL=$PROCESSOR_URL,CRITIC_URL=$CRITIC_URL"

echo "===================================================="
echo "All agents deployed successfully!"
echo "===================================================="

# Generate configuration for user_client.py
cat > cloud_config.py << EOL
# Cloud Run Configuration
# Generated by deploy_to_cloud_run.sh

MANAGER_URL = "$(cat url_manager.txt)/api/query"
SAFEGUARD_URL = "$(cat url_safeguard.txt)"
PROCESSOR_URL = "$(cat url_processor.txt)"
CRITIC_URL = "$(cat url_critic.txt)"
EOL

echo "Configuration for user_client.py has been generated in cloud_config.py"
echo "Use the cloud client with: python user_client_cloud.py"

# Cleanup Docker images and free disk space
if [ "$SKIP_CLEANUP" = false ]; then
  echo ""
  echo "===================================================="
  echo "Final Docker cleanup after deployment..."
  echo "===================================================="
  cleanup_docker
  echo ""
  echo "✓ Deployment completed successfully with Docker cleanup"
else
  echo ""
  echo "✓ Deployment completed successfully (Docker cleanup skipped)"
fi 