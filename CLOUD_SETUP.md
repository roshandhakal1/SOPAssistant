# Cloud Storage Integration Setup

## Google Drive Integration

### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Click "Create Project" and give it a name (e.g., "SOP Assistant")

### Step 2: Enable Google Drive API
1. In the Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "Google Drive API"
3. Click on it and press "Enable"

### Step 3: Create OAuth 2.0 Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure the OAuth consent screen first:
   - User Type: External (for personal use) or Internal (for organization)
   - Fill in app name, user support email, developer email
   - Add your domain if needed
4. For Application type, choose "Desktop application"
5. Give it a name (e.g., "SOP Assistant Desktop")
6. Click "Create"

### Step 4: Download Client Configuration
1. After creating the OAuth client, you'll see a dialog with the client ID and secret
2. Click "Download JSON" to download the credentials file
3. The file will look like this:
```json
{
  "installed": {
    "client_id": "your-client-id.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "your-client-secret",
    "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
  }
}
```

### Step 5: Organize Your SOP Files
1. Create a folder in Google Drive (e.g., "SOP Documents")
2. Upload all your SOP files (.pdf, .docx, .doc, .csv, .md) to this folder
3. Note the folder ID from the URL when viewing the folder in Google Drive

### Step 6: Connect in the App
1. Open your SOP Assistant app
2. Go to "📁 Document Management" in the sidebar
3. Find the "☁️ Google Drive Integration" section
4. Paste the JSON content from Step 4 into the configuration box
5. Click "Start Authentication"
6. Follow the OAuth flow to authorize access
7. Select your SOP folder
8. Click "Sync Documents"

## Benefits of Cloud Integration

✅ **Automatic Sync** - Files stay up-to-date automatically
✅ **Team Collaboration** - Share folders with team members  
✅ **Version Control** - Google Drive handles file versioning
✅ **No Manual Uploads** - Direct integration with your existing workflow
✅ **Backup & Security** - Files are safely stored in the cloud
✅ **Cross-Platform Access** - Access from any device

## Security Notes

- The app only requests READ-ONLY access to your Google Drive
- OAuth tokens are stored securely in your session
- No sensitive data is stored permanently
- You can disconnect at any time

## Alternative Options

### Microsoft OneDrive/SharePoint
- Similar setup with Microsoft Graph API
- Great for organizations using Office 365
- Contact support if you need this integration

### Dropbox
- Simple API integration available
- Good for smaller teams
- Contact support if you need this integration

## Troubleshooting

**Issue**: "Access blocked" error
**Solution**: Make sure OAuth consent screen is properly configured

**Issue**: "Invalid client configuration"  
**Solution**: Verify the JSON format and ensure all fields are present

**Issue**: "No documents found"
**Solution**: Check that your folder contains supported file types (.pdf, .docx, .doc, .csv, .md)