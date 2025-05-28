#!/bin/bash
# Script to set up Google Cloud Secret Manager secrets for A2A Double Validation

# Exit immediately if a command exits with a non-zero status
set -e

# Default values
PROJECT_ID=""
ENV_FILE=".env"

# Function to show usage
function show_usage {
  echo "Usage: $0 [options]"
  echo "Options:"
  echo "  -p, --project   Google Cloud Project ID (required)"
  echo "  -e, --env-file  Environment file to read secrets from (default: .env)"
  echo "  -h, --help      Show this help message"
  echo ""
  echo "This script will:"
  echo "  1. Read GOOGLE_API_KEY and HUGGINGFACE_TOKEN from your .env file"
  echo "  2. Create secrets in Google Cloud Secret Manager"
  echo "  3. Grant access permissions to the default compute service account"
  exit 1
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
    -e|--env-file)
      ENV_FILE="$2"
      shift
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
  echo "Error: Environment file $ENV_FILE not found"
  echo "Please create $ENV_FILE with your GOOGLE_API_KEY and HUGGINGFACE_TOKEN"
  exit 1
fi

# Load environment variables from file
echo "Loading secrets from $ENV_FILE..."
set -a  # automatically export all variables
source "$ENV_FILE"
set +a  # stop automatically exporting

# Validate that required secrets are present
if [[ -z "$GOOGLE_API_KEY" ]]; then
  echo "Error: GOOGLE_API_KEY not found in $ENV_FILE"
  exit 1
fi

if [[ -z "$HUGGINGFACE_TOKEN" ]]; then
  echo "Error: HUGGINGFACE_TOKEN not found in $ENV_FILE"
  exit 1
fi

echo "✓ Found GOOGLE_API_KEY in $ENV_FILE"
echo "✓ Found HUGGINGFACE_TOKEN in $ENV_FILE"

# Set the project
echo "Setting Google Cloud project to $PROJECT_ID"
gcloud config set project "$PROJECT_ID"

# Enable Secret Manager API if not already enabled
echo "Enabling Secret Manager API..."
gcloud services enable secretmanager.googleapis.com

# Create google-api-key secret
echo "Creating google-api-key secret..."
if gcloud secrets describe google-api-key >/dev/null 2>&1; then
  echo "Secret 'google-api-key' already exists. Adding new version..."
else
  gcloud secrets create google-api-key --replication-policy="automatic"
fi
echo -n "$GOOGLE_API_KEY" | gcloud secrets versions add google-api-key --data-file=-
echo "✓ google-api-key secret created/updated"

# Create huggingface-token secret
echo "Creating huggingface-token secret..."
if gcloud secrets describe huggingface-token >/dev/null 2>&1; then
  echo "Secret 'huggingface-token' already exists. Adding new version..."
else
  gcloud secrets create huggingface-token --replication-policy="automatic"
fi
echo -n "$HUGGINGFACE_TOKEN" | gcloud secrets versions add huggingface-token --data-file=-
echo "✓ huggingface-token secret created/updated"

# Get project number and service account
echo "Setting up permissions..."
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "Project Number: $PROJECT_NUMBER"
echo "Service Account: $SERVICE_ACCOUNT"

# Grant permissions for google-api-key
echo "Granting access to google-api-key secret..."
gcloud secrets add-iam-policy-binding google-api-key \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"

# Grant permissions for huggingface-token
echo "Granting access to huggingface-token secret..."
gcloud secrets add-iam-policy-binding huggingface-token \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"

echo ""
echo "===================================================="
echo "✅ Secrets setup completed successfully!"
echo "===================================================="
echo ""
echo "Created secrets:"
echo "  - google-api-key"
echo "  - huggingface-token"
echo ""
echo "Granted access to service account:"
echo "  - $SERVICE_ACCOUNT"
echo ""
echo "You can now run the deployment script:"
echo "  ./deploy_to_cloud_run.sh --project $PROJECT_ID" 