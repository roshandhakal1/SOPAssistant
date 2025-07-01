#!/bin/bash

# SOP Assistant - Google Cloud Run Deployment Script
# This script will deploy your app to Google Cloud Run with proper security

echo "🚀 SOP Assistant - Google Cloud Run Deployment"
echo "==============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Google Cloud CLI not found!${NC}"
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${YELLOW}🔐 Please login to Google Cloud first...${NC}"
    gcloud auth login
fi

# Get project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

if [ -z "$PROJECT_ID" ]; then
    echo -e "${YELLOW}📋 No project selected. Let's set one up...${NC}"
    echo "Enter your Google Cloud Project ID (or press Enter to create new):"
    read -r PROJECT_INPUT
    
    if [ -z "$PROJECT_INPUT" ]; then
        PROJECT_ID="sop-assistant-$(date +%s)"
        echo -e "${BLUE}📝 Creating new project: $PROJECT_ID${NC}"
        gcloud projects create $PROJECT_ID --name="SOP Assistant"
    else
        PROJECT_ID=$PROJECT_INPUT
    fi
    
    gcloud config set project $PROJECT_ID
fi

echo -e "${BLUE}📋 Using project: $PROJECT_ID${NC}"

# Enable required APIs
echo -e "${BLUE}🔧 Enabling required APIs...${NC}"
gcloud services enable run.googleapis.com cloudbuild.googleapis.com containerregistry.googleapis.com

# Deploy to Cloud Run
echo -e "${GREEN}🚀 Deploying to Google Cloud Run...${NC}"
gcloud run deploy sop-assistant \
    --source . \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 1 \
    --max-instances 10 \
    --timeout 3600 \
    --concurrency 10 \
    --set-env-vars="ENVIRONMENT=production"

# Get the service URL
SERVICE_URL=$(gcloud run services describe sop-assistant --platform=managed --region=us-central1 --format='value(status.url)')

echo ""
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}🌐 Your SOP Assistant is now available at:${NC}"
echo -e "${YELLOW}   $SERVICE_URL${NC}"
echo ""
echo -e "${BLUE}🔒 Security Benefits:${NC}"
echo "   ✅ Stateless containers (no session leakage)"
echo "   ✅ Isolated user sessions"
echo "   ✅ Enterprise-grade security"
echo "   ✅ Auto-scaling based on demand"
echo ""
echo -e "${BLUE}💰 Cost Benefits:${NC}"
echo "   ✅ Pay only for actual usage"
echo "   ✅ Scales to zero when not used"
echo "   ✅ No idle server costs"
echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo "   1. Test the application from multiple devices"
echo "   2. Verify authentication works correctly"
echo "   3. Set up your admin account"
echo "   4. Sync your documents via Admin Portal"
echo ""
echo -e "${GREEN}🎉 Enjoy your secure, scalable SOP Assistant!${NC}"