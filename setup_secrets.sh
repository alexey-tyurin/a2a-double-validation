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
  echo ""
  echo "Note: This script should be run with a user account that has Secret Manager Admin permissions"
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

# Check current authentication
echo "Checking current authentication..."
CURRENT_ACCOUNT=$(gcloud config get-value account 2>/dev/null || echo "")
if [[ -z "$CURRENT_ACCOUNT" ]]; then
  echo "Error: No authenticated account found."
  echo "Please run: gcloud auth login"
  exit 1
fi

echo "Current authenticated account: $CURRENT_ACCOUNT"

# Check if current account is a service account
if [[ "$CURRENT_ACCOUNT" == *"@"*".gserviceaccount.com" ]]; then
  echo "Warning: You are authenticated as a service account: $CURRENT_ACCOUNT"
  echo "Service accounts typically don't have permission to grant IAM policies."
  echo "Please authenticate with a user account that has Secret Manager Admin role:"
  echo "  gcloud auth login"
  echo ""
  read -p "Do you want to continue anyway? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Exiting. Please authenticate with a user account and try again."
    exit 1
  fi
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

# Function to create or update a secret
create_or_update_secret() {
  local secret_name="$1"
  local secret_value="$2"
  
  echo "Processing secret: $secret_name"
  
  # Check if secret exists
  if gcloud secrets describe "$secret_name" --project="$PROJECT_ID" >/dev/null 2>&1; then
    echo "Secret '$secret_name' already exists. Adding new version..."
    echo -n "$secret_value" | gcloud secrets versions add "$secret_name" --data-file=- --project="$PROJECT_ID"
  else
    echo "Creating new secret: $secret_name"
    gcloud secrets create "$secret_name" --replication-policy="automatic" --project="$PROJECT_ID"
    echo "Adding secret value..."
    echo -n "$secret_value" | gcloud secrets versions add "$secret_name" --data-file=- --project="$PROJECT_ID"
  fi
  echo "✓ Secret '$secret_name' created/updated successfully"
}

# Create google-api-key secret
echo "Creating google-api-key secret..."
create_or_update_secret "google-api-key" "$GOOGLE_API_KEY"

# Create huggingface-token secret
echo "Creating huggingface-token secret..."
create_or_update_secret "huggingface-token" "$HUGGINGFACE_TOKEN"

# Get project number and service account
echo "Setting up permissions..."
echo "Getting project number for project: $PROJECT_ID"
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "Project Number: $PROJECT_NUMBER"
echo "Service Account: $SERVICE_ACCOUNT"

# Grant permissions for google-api-key
echo "Granting access to google-api-key secret..."
if gcloud secrets add-iam-policy-binding google-api-key \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor" \
  --project="$PROJECT_ID" 2>/dev/null; then
  echo "✓ Permissions granted for google-api-key"
else
  echo "❌ Failed to grant permissions for google-api-key"
  echo "You may need to run this command manually with an account that has Secret Manager Admin role:"
  echo "gcloud secrets add-iam-policy-binding google-api-key --member=\"serviceAccount:${SERVICE_ACCOUNT}\" --role=\"roles/secretmanager.secretAccessor\" --project=\"$PROJECT_ID\""
fi

# Grant permissions for huggingface-token
echo "Granting access to huggingface-token secret..."
if gcloud secrets add-iam-policy-binding huggingface-token \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor" \
  --project="$PROJECT_ID" 2>/dev/null; then
  echo "✓ Permissions granted for huggingface-token"
else
  echo "❌ Failed to grant permissions for huggingface-token"
  echo "You may need to run this command manually with an account that has Secret Manager Admin role:"
  echo "gcloud secrets add-iam-policy-binding huggingface-token --member=\"serviceAccount:${SERVICE_ACCOUNT}\" --role=\"roles/secretmanager.secretAccessor\" --project=\"$PROJECT_ID\""
fi

echo ""
echo "===================================================="
echo "✅ Secrets setup completed!"
echo "===================================================="
echo ""
echo "Created secrets:"
echo "  - google-api-key"
echo "  - huggingface-token"
echo ""
echo "Target service account:"
echo "  - $SERVICE_ACCOUNT"
echo ""
echo "If permission granting failed, you can:"
echo "1. Authenticate with a user account: gcloud auth login"
echo "2. Or grant permissions manually in the Google Cloud Console"
echo ""
echo "You can now run the deployment script:"
echo "  ./deploy_to_cloud_run.sh --project $PROJECT_ID" 