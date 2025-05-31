#!/bin/bash
# Script to check the status of A2A Cloud Run services

# Exit immediately if a command exits with a non-zero status
set -e

# Default values
PROJECT_ID=""
REGION="us-central1"

# Function to show usage
function show_usage {
  echo "Usage: $0 [options]"
  echo "Options:"
  echo "  -p, --project     Google Cloud Project ID (required)"
  echo "  -r, --region      Google Cloud Region (default: us-central1)"
  echo "  -h, --help        Show this help message"
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
echo "Checking Cloud Run services in project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

gcloud config set project "$PROJECT_ID"

# Array of service names
services=("a2a-manager-agent" "a2a-safeguard-agent" "a2a-processor-agent" "a2a-critic-agent")

echo "===================================================="
echo "A2A Cloud Run Services Status"
echo "===================================================="

# Check overall services list
echo "📋 All Cloud Run services in region $REGION:"
gcloud run services list --region="$REGION" --filter="metadata.name:(a2a-)" --format="table(metadata.name,status.url,status.conditions[0].status,status.conditions[0].reason)" || echo "No A2A services found or error listing services"

echo ""
echo "===================================================="
echo "Detailed Status for Each A2A Service"
echo "===================================================="

for service in "${services[@]}"; do
  echo ""
  echo "🔍 Checking $service..."
  
  # Check if service exists
  if gcloud run services describe "$service" --region="$REGION" --format="value(metadata.name)" >/dev/null 2>&1; then
    
    # Get service details
    service_url=$(gcloud run services describe "$service" --region="$REGION" --format="value(status.url)" 2>/dev/null || echo "URL not available")
    service_status=$(gcloud run services describe "$service" --region="$REGION" --format="value(status.conditions[0].status)" 2>/dev/null || echo "Unknown")
    service_reason=$(gcloud run services describe "$service" --region="$REGION" --format="value(status.conditions[0].reason)" 2>/dev/null || echo "Unknown")
    latest_revision=$(gcloud run services describe "$service" --region="$REGION" --format="value(status.latestReadyRevisionName)" 2>/dev/null || echo "Unknown")
    
    echo "  ✅ Service exists"
    echo "  📍 URL: $service_url"
    echo "  🔄 Status: $service_status"
    echo "  💭 Reason: $service_reason"
    echo "  📦 Latest Revision: $latest_revision"
    
    # Check if service is ready and test endpoint
    if [[ "$service_status" == "True" && "$service_url" != "URL not available" ]]; then
      echo "  🧪 Testing endpoint..."
      
      if [[ "$service" == "a2a-manager-agent" ]]; then
        # Test manager agent API endpoint
        if curl -s --max-time 10 "$service_url" >/dev/null 2>&1; then
          echo "  ✅ Endpoint responding"
        else
          echo "  ❌ Endpoint not responding"
        fi
      else
        # Test A2A endpoint for other agents
        if curl -s --max-time 10 "$service_url/.well-known/agent.json" >/dev/null 2>&1; then
          echo "  ✅ A2A endpoint responding"
        else
          echo "  ❌ A2A endpoint not responding"
        fi
      fi
    else
      echo "  ⚠️  Service not ready - endpoint test skipped"
    fi
    
  else
    echo "  ❌ Service not found"
  fi
  
  echo "  ----------------------------------------"
done

echo ""
echo "===================================================="
echo "Service URLs Summary"
echo "===================================================="

# Generate service URLs for easy access
for service in "${services[@]}"; do
  service_url=$(gcloud run services describe "$service" --region="$REGION" --format="value(status.url)" 2>/dev/null || echo "Not deployed")
  if [[ "$service" == "a2a-manager-agent" && "$service_url" != "Not deployed" ]]; then
    echo "🌐 Manager API: $service_url/api/query"
  elif [[ "$service_url" != "Not deployed" ]]; then
    echo "🔗 $service: $service_url"
  else
    echo "❌ $service: Not deployed"
  fi
done

echo ""
echo "✅ Status check completed!"
echo ""
echo "💡 Tips:"
echo "   - Use 'gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=SERVICE_NAME\" --limit=50' to view logs"
echo "   - Use './kill_cloud_services.sh --project $PROJECT_ID' to stop all services"
echo "   - Use './deploy_to_cloud_run.sh --project $PROJECT_ID' to redeploy" 