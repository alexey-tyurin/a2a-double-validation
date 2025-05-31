#!/bin/bash
# Script to stop/delete A2A Cloud Run services

# Exit immediately if a command exits with a non-zero status
set -e

# Default values
PROJECT_ID=""
REGION="us-central1"
FORCE=false

# Function to show usage
function show_usage {
  echo "Usage: $0 [options]"
  echo "Options:"
  echo "  -p, --project     Google Cloud Project ID (required)"
  echo "  -r, --region      Google Cloud Region (default: us-central1)"
  echo "  -f, --force       Force deletion without confirmation"
  echo "  -h, --help        Show this help message"
  echo ""
  echo "This script will delete the following Cloud Run services:"
  echo "  - a2a-manager-agent"
  echo "  - a2a-safeguard-agent"
  echo "  - a2a-processor-agent"
  echo "  - a2a-critic-agent"
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
    -r|--region)
      REGION="$2"
      shift
      shift
      ;;
    -f|--force)
      FORCE=true
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

# Set the project
echo "Managing Cloud Run services in project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

gcloud config set project "$PROJECT_ID"

# Array of service names
services=("a2a-manager-agent" "a2a-safeguard-agent" "a2a-processor-agent" "a2a-critic-agent")

# Check which services exist
existing_services=()
echo "🔍 Checking which A2A services exist..."
for service in "${services[@]}"; do
  if gcloud run services describe "$service" --region="$REGION" --format="value(metadata.name)" >/dev/null 2>&1; then
    existing_services+=("$service")
    echo "  ✅ Found: $service"
  else
    echo "  ❌ Not found: $service"
  fi
done

if [[ ${#existing_services[@]} -eq 0 ]]; then
  echo ""
  echo "ℹ️  No A2A Cloud Run services found in region $REGION"
  echo "Nothing to delete."
  exit 0
fi

echo ""
echo "===================================================="
echo "Services to be deleted:"
echo "===================================================="
for service in "${existing_services[@]}"; do
  service_url=$(gcloud run services describe "$service" --region="$REGION" --format="value(status.url)" 2>/dev/null || echo "Unknown")
  echo "🗑️  $service ($service_url)"
done

# Confirmation prompt (unless force is used)
if [[ "$FORCE" != true ]]; then
  echo ""
  echo "⚠️  WARNING: This will permanently delete ${#existing_services[@]} Cloud Run service(s)."
  echo "This action cannot be undone."
  echo ""
  read -p "Are you sure you want to continue? (yes/no): " -r
  echo
  if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "❌ Operation canceled by user"
    exit 1
  fi
fi

echo ""
echo "===================================================="
echo "Deleting Cloud Run Services"
echo "===================================================="

# Delete each service
deleted_count=0
failed_count=0

for service in "${existing_services[@]}"; do
  echo ""
  echo "🗑️  Deleting $service..."
  
  if gcloud run services delete "$service" --region="$REGION" --quiet; then
    echo "  ✅ Successfully deleted $service"
    ((deleted_count++))
  else
    echo "  ❌ Failed to delete $service"
    ((failed_count++))
  fi
done

echo ""
echo "===================================================="
echo "Cleanup Summary"
echo "===================================================="
echo "✅ Successfully deleted: $deleted_count service(s)"
if [[ $failed_count -gt 0 ]]; then
  echo "❌ Failed to delete: $failed_count service(s)"
fi

# Cleanup temporary files
echo ""
echo "🧹 Cleaning up temporary files..."
temp_files=("url_manager.txt" "url_safeguard.txt" "url_processor.txt" "url_critic.txt" "cloud_config.py")
cleaned_files=0

for file in "${temp_files[@]}"; do
  if [[ -f "$file" ]]; then
    rm -f "$file"
    echo "  🗑️  Removed: $file"
    ((cleaned_files++))
  fi
done

if [[ $cleaned_files -eq 0 ]]; then
  echo "  ℹ️  No temporary files found to clean"
else
  echo "  ✅ Cleaned up $cleaned_files temporary file(s)"
fi

echo ""
if [[ $failed_count -eq 0 ]]; then
  echo "🎉 All A2A Cloud Run services have been successfully deleted!"
else
  echo "⚠️  Deletion completed with $failed_count error(s). Check the output above for details."
fi

echo ""
echo "💡 Tips:"
echo "   - Use './check_cloud_status.sh --project $PROJECT_ID' to verify deletion"
echo "   - Use './deploy_to_cloud_run.sh --project $PROJECT_ID' to redeploy"
echo "   - Check Cloud Console for any remaining resources" 