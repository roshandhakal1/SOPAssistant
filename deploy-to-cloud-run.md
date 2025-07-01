# Deploy SOP Assistant to Google Cloud Run

## Why Google Cloud Run?

✅ **Stateless containers** - No session leakage between users  
✅ **Enterprise security** - Proper isolation  
✅ **Auto-scaling** - Handle multiple users efficiently  
✅ **Cost-effective** - Pay only for actual usage  
✅ **Fixes authentication issues** - No persistent storage problems  

## Prerequisites

1. **Google Cloud Account** with billing enabled
2. **Google Cloud CLI** installed locally
3. **Docker** installed (for local testing)

## Quick Deploy Steps

### 1. Setup Google Cloud Project

```bash
# Install Google Cloud CLI if not already installed
# https://cloud.google.com/sdk/docs/install

# Login to Google Cloud
gcloud auth login

# Create new project (or use existing)
gcloud projects create sop-assistant-prod --name="SOP Assistant"

# Set project
gcloud config set project sop-assistant-prod

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### 2. Deploy from Local Directory

```bash
# Navigate to your project directory
cd /Users/roshandhakal/Desktop/AD/Gemini

# Deploy directly to Cloud Run (easiest method)
gcloud run deploy sop-assistant \
    --source . \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 1 \
    --max-instances 10 \
    --timeout 3600
```

### 3. Alternative: Manual Docker Build

```bash
# Build container locally
docker build -t gcr.io/sop-assistant-prod/sop-assistant .

# Push to Google Container Registry
docker push gcr.io/sop-assistant-prod/sop-assistant

# Deploy to Cloud Run
gcloud run deploy sop-assistant \
    --image gcr.io/sop-assistant-prod/sop-assistant \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated
```

## Configuration

### Environment Variables (if needed)

```bash
# Set environment variables for the service
gcloud run services update sop-assistant \
    --region us-central1 \
    --set-env-vars="ENVIRONMENT=production,DEBUG=false"
```

### Custom Domain (optional)

```bash
# Map custom domain
gcloud run domain-mappings create \
    --service sop-assistant \
    --domain your-domain.com \
    --region us-central1
```

## Security Benefits

🔒 **No session persistence issues**  
🔒 **Isolated user sessions**  
🔒 **No shared file systems**  
🔒 **Environment variables properly scoped**  
🔒 **Enterprise-grade security**  

## Monitoring

```bash
# View logs
gcloud run services logs tail sop-assistant --region us-central1

# Check service status
gcloud run services describe sop-assistant --region us-central1
```

## Cost Optimization

- **CPU allocation**: Only during requests
- **Memory**: Optimized for your usage
- **Auto-scaling**: Scales to zero when not used
- **No idle costs**: Unlike Render's always-on pricing

## Next Steps

1. Deploy using the commands above
2. Test authentication from multiple devices/browsers
3. Verify no session leakage occurs
4. Set up custom domain if needed
5. Configure monitoring and alerts

The authentication issues you experienced with Render should be completely resolved with Cloud Run's stateless architecture!