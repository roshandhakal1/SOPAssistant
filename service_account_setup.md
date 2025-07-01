# Alternative: Service Account Setup (Simpler)

If you're having trouble with OAuth, use a service account instead:

## Step 1: Create Service Account
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Go to **"IAM & Admin"** → **"Service Accounts"**
4. Click **"+ CREATE SERVICE ACCOUNT"**
5. Fill in:
   - **Service account name**: `sop-assistant-reader`
   - **Service account ID**: (auto-filled)
   - **Description**: `Reads SOP documents from Google Drive`
6. Click **"CREATE AND CONTINUE"**
7. Skip the roles (click **"CONTINUE"**)
8. Skip user access (click **"DONE"**)

## Step 2: Create Key
1. Click on the service account you just created
2. Go to **"KEYS"** tab
3. Click **"ADD KEY"** → **"Create new key"**
4. Choose **"JSON"** format
5. Click **"CREATE"**
6. Save the downloaded JSON file

## Step 3: Share Your Google Drive Folder
1. Go to Google Drive
2. Right-click your SOP folder
3. Click **"Share"**
4. Add the service account email (from the JSON file, looks like: `sop-assistant-reader@your-project.iam.gserviceaccount.com`)
5. Give it **"Viewer"** permission
6. Click **"Send"**

## Step 4: Use in App
The service account can now read your folder without OAuth flow!