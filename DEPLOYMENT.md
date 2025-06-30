# 🚀 SOP Assistant Deployment Guide

## Quick Deployment Options

### Option 1: Streamlit Cloud (Recommended - Free & Easy)

1. **Fork/Clone Repository**
   - Ensure your repository is public or you have Streamlit Cloud access

2. **Get Google Gemini API Key**
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Copy the key for use in secrets

3. **Deploy to Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Connect your GitHub account
   - Select repository: `roshandhakal1/gemini`
   - Main file path: `app.py`
   - Click "Deploy"

4. **Configure Secrets**
   - In Streamlit Cloud dashboard, go to your app
   - Click "Settings" → "Secrets"
   - Add the following secrets:
   ```toml
   GEMINI_API_KEY = "your_actual_gemini_api_key_here"
   ADMIN_USERNAME = "your_admin_username"
   ADMIN_PASSWORD = "your_secure_admin_password"
   USER_USERNAME = "your_user_username"
   USER_PASSWORD = "your_secure_user_password"
   SOP_FOLDER = "/mount/src/sops"
   CHROMA_PERSIST_DIR = "/mount/src/chroma_db"
   ```

5. **Upload SOP Documents**
   - Use the app's upload feature to add your SOPs
   - Or add them to a `sops/` folder in your repository

### Option 2: Heroku

1. **Install Heroku CLI**
   ```bash
   # macOS
   brew tap heroku/brew && brew install heroku
   
   # Or download from heroku.com
   ```

2. **Create Heroku App**
   ```bash
   heroku create your-sop-assistant
   heroku config:set GEMINI_API_KEY="your_api_key"
   heroku config:set ADMIN_USERNAME="admin"
   heroku config:set ADMIN_PASSWORD="your_secure_password"
   git push heroku main
   ```

3. **Create Procfile**
   ```
   web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
   ```

### Option 3: Docker

1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY . .
   
   EXPOSE 8501
   
   HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health
   
   ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
   ```

2. **Build and Run**
   ```bash
   docker build -t sop-assistant .
   docker run -p 8501:8501 \
     -e GEMINI_API_KEY="your_api_key" \
     -e ADMIN_PASSWORD="your_password" \
     sop-assistant
   ```

### Option 4: AWS/GCP/Azure

1. **AWS EC2**
   - Launch Ubuntu instance
   - Install Python, git, requirements
   - Use nginx as reverse proxy
   - Set up SSL with Let's Encrypt

2. **Google Cloud Run**
   - Build Docker image
   - Deploy to Cloud Run
   - Configure environment variables

3. **Azure Container Instances**
   - Build and push to Azure Container Registry
   - Deploy container instance
   - Configure secrets in Key Vault

## Security Configuration

### Production Secrets
**Never use default passwords in production!**

```toml
# Strong password examples
ADMIN_PASSWORD = "MySecure@dminP@ssw0rd2024!"
USER_PASSWORD = "SecureUser!Pass123#"
```

### Environment Variables Required
- `GEMINI_API_KEY`: Google Gemini API key
- `ADMIN_USERNAME`: Admin username (default: admin)
- `ADMIN_PASSWORD`: Admin password (default: admin123)
- `USER_USERNAME`: User username (default: user)  
- `USER_PASSWORD`: User password (default: user123)

### Optional Configuration
- `SOP_FOLDER`: Path to SOP documents
- `CHROMA_PERSIST_DIR`: Database storage path

## Post-Deployment Steps

1. **Test Authentication**
   - Try logging in with admin and user accounts
   - Verify session timeout works (4 hours)

2. **Upload SOPs**
   - Use the document upload feature
   - Or place files in the configured SOP folder

3. **Test Both Modes**
   - Knowledge Search mode
   - Expert Consultant mode

4. **Monitor Usage**
   - Check Streamlit Cloud metrics
   - Monitor API usage on Google AI Studio

## Troubleshooting

### Common Issues

1. **"Invalid API key" error**
   - Verify GEMINI_API_KEY is correct
   - Check API key has proper permissions

2. **"No documents found"**
   - Upload SOPs through the interface
   - Check SOP_FOLDER path is correct

3. **Authentication not working**
   - Verify secrets are properly set
   - Check username/password configuration

4. **Performance issues**
   - Consider upgrading Streamlit Cloud plan
   - Optimize document chunking size

### Support
- Check application logs in your deployment platform
- Review Streamlit Cloud deployment logs
- Verify all required secrets are configured

## Cost Considerations

### Streamlit Cloud
- **Free tier**: Perfect for small teams
- **Pro tier**: $20/month for more resources

### Google Gemini API
- Pay-per-use pricing
- Free tier includes generous limits
- Monitor usage in Google AI Studio

### Other Platforms
- Heroku: ~$7/month for basic dyno
- AWS/GCP/Azure: Variable based on usage