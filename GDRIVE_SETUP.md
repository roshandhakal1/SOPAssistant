# Google Drive Persistent Authentication Setup

Since you're getting asked to authenticate every time, here's how to set up persistent authentication:

## Option 1: Add to Render Environment Variables (Recommended)

After you authenticate once in the app:

1. Go to your **Render Dashboard**
2. Select your **SOP Assistant** service  
3. Go to **Environment** tab
4. Add these environment variables (you'll get these values after authenticating once):

```
GDRIVE_TOKEN=your_access_token_here
GDRIVE_REFRESH_TOKEN=your_refresh_token_here  
GDRIVE_CLIENT_ID=your_client_id_here
GDRIVE_CLIENT_SECRET=your_client_secret_here
```

## Option 2: Use OAuth Client JSON (Easier)

1. Go to **Render Dashboard** → **Environment** tab
2. Add one environment variable:

```
GDRIVE_CLIENT_CONFIG={"installed":{"client_id":"YOUR_CLIENT_ID","client_secret":"YOUR_CLIENT_SECRET","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","redirect_uris":["urn:ietf:wg:oauth:2.0:oob","http://localhost"]}}
```

Replace YOUR_CLIENT_ID and YOUR_CLIENT_SECRET with your actual values.

## After Setting Environment Variables:

The app will automatically:
- Use stored credentials on startup
- Refresh tokens when needed  
- Never ask for authentication again
- Work across all deployments

This way you authenticate once and it remembers forever!