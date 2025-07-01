import os
import io
import json
from pathlib import Path
from typing import List, Dict, Optional
import streamlit as st
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import tempfile

class GoogleDriveManager:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
        self.credentials = None
        self.service = None
        
        # Auto-load credentials on initialization
        self.load_saved_credentials()
        
    def setup_oauth_flow(self, client_config: Dict) -> str:
        """Setup OAuth flow and return authorization URL"""
        # Try with the simplest redirect URI that should work
        redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
        
        # Check if the config has redirect_uris and use the first one
        if 'installed' in client_config and 'redirect_uris' in client_config['installed']:
            redirect_uris = client_config['installed']['redirect_uris']
            if redirect_uris and len(redirect_uris) > 0:
                redirect_uri = redirect_uris[0]
        
        flow = Flow.from_client_config(
            client_config,
            scopes=self.SCOPES,
            redirect_uri=redirect_uri
        )
        
        auth_url, _ = flow.authorization_url(
            prompt='consent',
            access_type='offline'
        )
        return auth_url, flow
    
    def authenticate_with_code(self, flow: Flow, auth_code: str) -> bool:
        """Complete OAuth flow with authorization code"""
        try:
            flow.fetch_token(code=auth_code)
            self.credentials = flow.credentials
            self.service = build('drive', 'v3', credentials=self.credentials)
            
            # Save credentials to session state and persistent storage
            cred_data = {
                'token': self.credentials.token,
                'refresh_token': self.credentials.refresh_token,
                'token_uri': self.credentials.token_uri,
                'client_id': self.credentials.client_id,
                'client_secret': self.credentials.client_secret,
                'scopes': self.credentials.scopes
            }
            st.session_state.gdrive_credentials = cred_data
            
            # Save to multiple persistent locations
            try:
                # Method 1: Streamlit session state (primary)
                st.session_state._persistent_gdrive_creds = cred_data
                
                # Method 2: Environment variable (works on cloud deployments)
                os.environ['GDRIVE_CREDENTIALS'] = json.dumps(cred_data)
                
                # Method 3: File storage (fallback)
                with open('.gdrive_credentials.json', 'w') as f:
                    json.dump(cred_data, f)
                    
            except Exception as e:
                st.warning(f"Could not save credentials persistently: {e}")
            return True
        except Exception as e:
            st.error(f"Authentication failed: {str(e)}")
            return False
    
    def load_saved_credentials(self) -> bool:
        """Load credentials from session state or persistent storage"""
        cred_data = None
        
        # Try session state first
        if 'gdrive_credentials' in st.session_state:
            cred_data = st.session_state.gdrive_credentials
        else:
            # Try multiple storage locations
            import json
            import os
            
            # Try persistent session state (most reliable)
            if hasattr(st.session_state, '_persistent_gdrive_creds'):
                cred_data = st.session_state._persistent_gdrive_creds
                st.session_state.gdrive_credentials = cred_data
            
            # Try environment variable (works on cloud deployments)
            if not cred_data and 'GDRIVE_CREDENTIALS' in os.environ:
                try:
                    cred_data = json.loads(os.environ['GDRIVE_CREDENTIALS'])
                    st.session_state.gdrive_credentials = cred_data
                    st.session_state._persistent_gdrive_creds = cred_data
                except Exception:
                    pass
            
            # Try file storage (fallback)
            if not cred_data:
                try:
                    with open('.gdrive_credentials.json', 'r') as f:
                        cred_data = json.load(f)
                        st.session_state.gdrive_credentials = cred_data
                        st.session_state._persistent_gdrive_creds = cred_data
                except Exception:
                    pass
            
            # Try Streamlit secrets (if available)
            if not cred_data:
                try:
                    if hasattr(st, 'secrets') and 'gdrive_credentials' in st.secrets:
                        cred_data = dict(st.secrets.gdrive_credentials)
                        st.session_state.gdrive_credentials = cred_data
                        st.session_state._persistent_gdrive_creds = cred_data
                except Exception:
                    pass
        
        if cred_data:
            self.credentials = Credentials(
                token=cred_data['token'],
                refresh_token=cred_data['refresh_token'],
                token_uri=cred_data['token_uri'],
                client_id=cred_data['client_id'],
                client_secret=cred_data['client_secret'],
                scopes=cred_data['scopes']
            )
            
            # Refresh if needed
            if self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
                # Update all storage methods with new token
                cred_data['token'] = self.credentials.token
                st.session_state.gdrive_credentials = cred_data
                st.session_state._persistent_gdrive_creds = cred_data
                
                # Update environment variable
                try:
                    os.environ['GDRIVE_CREDENTIALS'] = json.dumps(cred_data)
                except Exception:
                    pass
                
                # Update file storage
                try:
                    with open('.gdrive_credentials.json', 'w') as f:
                        json.dump(cred_data, f)
                except Exception:
                    pass
            
            self.service = build('drive', 'v3', credentials=self.credentials)
            return True
        return False
    
    def list_folders(self, parent_folder_id: Optional[str] = None) -> List[Dict]:
        """List folders in Google Drive with pagination support"""
        if not self.service:
            return []
        
        try:
            query = "mimeType='application/vnd.google-apps.folder'"
            if parent_folder_id:
                query += f" and '{parent_folder_id}' in parents"
            
            all_folders = []
            page_token = None
            
            # Get all folders with pagination
            while True:
                request_params = {
                    'q': query,
                    'fields': "nextPageToken, files(id, name, parents)",
                    'pageSize': 1000  # Maximum allowed
                }
                
                if page_token:
                    request_params['pageToken'] = page_token
                
                results = self.service.files().list(**request_params).execute()
                
                folders = results.get('files', [])
                all_folders.extend(folders)
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
            
            return all_folders
        except Exception as e:
            st.error(f"Error listing folders: {str(e)}")
            return []
    
    def list_documents(self, folder_id: str) -> List[Dict]:
        """List documents in a specific folder with pagination support"""
        if not self.service:
            return []
        
        try:
            # Query for supported document types
            mime_types = [
                "application/pdf",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
                "application/msword",  # .doc
                "text/csv",
                "text/markdown",
                "text/plain",
                "application/vnd.google-apps.document",  # Google Docs
                "application/rtf",  # RTF files
                "application/vnd.oasis.opendocument.text"  # ODT files
            ]
            
            query = f"'{folder_id}' in parents and ("
            query += " or ".join([f"mimeType='{mime}'" for mime in mime_types])
            query += ")"
            
            all_files = []
            page_token = None
            
            # Get all files with pagination
            while True:
                request_params = {
                    'q': query,
                    'fields': "nextPageToken, files(id, name, mimeType, size, modifiedTime)",
                    'pageSize': 1000  # Maximum allowed
                }
                
                if page_token:
                    request_params['pageToken'] = page_token
                
                results = self.service.files().list(**request_params).execute()
                
                files = results.get('files', [])
                all_files.extend(files)
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
            
            return all_files
        except Exception as e:
            st.error(f"Error listing documents: {str(e)}")
            return []
    
    def download_file(self, file_id: str, file_name: str, local_folder: str) -> Optional[Dict]:
        """Download a file from Google Drive and return path with metadata"""
        if not self.service:
            return None
        
        try:
            request = self.service.files().get_media(fileId=file_id)
            
            # Create local file path
            local_path = Path(local_folder) / file_name
            
            # Download file
            with open(local_path, 'wb') as local_file:
                downloader = MediaIoBaseDownload(local_file, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
            
            # Return path and metadata
            return {
                'path': str(local_path),
                'gdrive_id': file_id,
                'gdrive_link': f"https://drive.google.com/file/d/{file_id}/view"
            }
        except Exception as e:
            st.error(f"Error downloading {file_name}: {str(e)}")
            return None
    
    def sync_folder(self, folder_id: str, local_folder: str) -> List[Dict]:
        """Sync entire folder from Google Drive"""
        if not self.service:
            return []
        
        # Ensure local folder exists
        Path(local_folder).mkdir(parents=True, exist_ok=True)
        
        # Get list of documents
        documents = self.list_documents(folder_id)
        downloaded_files = []
        
        for doc in documents:
            file_info = self.download_file(doc['id'], doc['name'], local_folder)
            if file_info:
                downloaded_files.append(file_info)
                
                # Save Google Drive metadata
                metadata_path = Path(file_info['path'] + '.gdrive_metadata')
                with open(metadata_path, 'w') as f:
                    json.dump({
                        'gdrive_id': doc['id'],
                        'gdrive_link': f"https://drive.google.com/file/d/{doc['id']}/view",
                        'gdrive_name': doc['name']
                    }, f)
        
        return downloaded_files

class CloudStorageUI:
    def __init__(self):
        self.gdrive = GoogleDriveManager()
    
    def render_google_drive_setup(self):
        """Render Google Drive setup UI"""
        st.subheader("☁️ Google Drive Integration")
        
        # Show configured folder info
        from config import Config
        config = Config()
        if config.GOOGLE_DRIVE_FOLDER_ID:
            st.info(f"📂 **Main Folder**: Gemini Training (`{config.GOOGLE_DRIVE_FOLDER_ID}`)")
            
            # Show subfolders in the main folder
            if self.gdrive.load_saved_credentials():
                st.subheader("📁 Choose Subfolder to Sync")
                
                # List subfolders
                subfolders = self.gdrive.list_folders(config.GOOGLE_DRIVE_FOLDER_ID)
                if subfolders:
                    # Add option to sync main folder directly
                    folder_options = {"📂 Main Folder (Gemini Training)": config.GOOGLE_DRIVE_FOLDER_ID}
                    for folder in subfolders:
                        folder_options[f"📁 {folder['name']}"] = folder['id']
                    
                    selected_sync_folder = st.selectbox(
                        "Select folder to sync documents from:",
                        options=list(folder_options.keys()),
                        key="sync_folder_selection"
                    )
                    
                    if selected_sync_folder:
                        folder_id = folder_options[selected_sync_folder]
                        
                        # Show documents in selected folder
                        documents = self.gdrive.list_documents(folder_id)
                        if documents:
                            st.info(f"📄 Found {len(documents)} documents in this folder")
                            
                            # Debug button to verify pagination is working
                            if st.button(f"🔍 Debug: Verify Document Count", key=f"debug_docs_{folder_id}"):
                                try:
                                    # Show pagination details
                                    st.write("**Pagination Test Results:**")
                                    
                                    # Test with different page sizes
                                    test_sizes = [100, 500, 1000]
                                    for page_size in test_sizes:
                                        all_files = []
                                        page_token = None
                                        page_count = 0
                                        
                                        while True:
                                            page_count += 1
                                            request_params = {
                                                'q': f"'{folder_id}' in parents",
                                                'fields': "nextPageToken, files(id, name, mimeType)",
                                                'pageSize': page_size
                                            }
                                            
                                            if page_token:
                                                request_params['pageToken'] = page_token
                                            
                                            results = self.gdrive.service.files().list(**request_params).execute()
                                            
                                            files = results.get('files', [])
                                            all_files.extend(files)
                                            
                                            page_token = results.get('nextPageToken')
                                            if not page_token:
                                                break
                                        
                                        st.write(f"- Page size {page_size}: {len(all_files)} total files in {page_count} pages")
                                    
                                    # Show file type breakdown
                                    mime_counts = {}
                                    supported_count = 0
                                    supported_types = [
                                        "application/pdf",
                                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                        "application/msword",
                                        "text/csv",
                                        "text/markdown",
                                        "text/plain",
                                        "application/vnd.google-apps.document",
                                        "application/rtf",
                                        "application/vnd.oasis.opendocument.text"
                                    ]
                                    
                                    for file in all_files:
                                        mime_type = file.get('mimeType', 'unknown')
                                        mime_counts[mime_type] = mime_counts.get(mime_type, 0) + 1
                                        if mime_type in supported_types:
                                            supported_count += 1
                                    
                                    st.write(f"**Supported documents**: {supported_count}")
                                    st.write(f"**Total files**: {len(all_files)}")
                                    st.write("**File types breakdown:**")
                                    for mime_type, count in sorted(mime_counts.items()):
                                        status = "✅ Supported" if mime_type in supported_types else "❌ Not supported"
                                        st.write(f"- {mime_type}: {count} files ({status})")
                                        
                                except Exception as e:
                                    st.error(f"Debug error: {e}")
                            
                            if st.button("🚀 Sync from Selected Folder", type="primary"):
                                with st.spinner(f"Syncing from {selected_sync_folder}..."):
                                    downloaded_files = self.gdrive.sync_folder(folder_id, "./documents")
                                    if downloaded_files:
                                        st.success(f"✅ Synced {len(downloaded_files)} documents!")
                                        
                                        # Save this folder as the preferred sync folder
                                        st.session_state.preferred_sync_folder = folder_id
                                        
                                        # Show synced files with links
                                        with st.expander("View Synced Documents", expanded=True):
                                            for file_info in downloaded_files:
                                                col1, col2 = st.columns([3, 1])
                                                with col1:
                                                    st.text(f"📄 {Path(file_info['path']).name}")
                                                with col2:
                                                    st.markdown(f"[Open in Drive]({file_info['gdrive_link']})")
                        else:
                            st.warning("No supported documents found in this folder")
                            
                            # Debug option for subfolders
                            if st.button(f"🔍 Debug: Show All Files in {selected_sync_folder.split(' ')[-1]}", key=f"debug_{folder_id}"):
                                try:
                                    # Use pagination to get ALL files
                                    all_files = []
                                    page_token = None
                                    
                                    while True:
                                        request_params = {
                                            'q': f"'{folder_id}' in parents",
                                            'fields': "nextPageToken, files(id, name, mimeType, size)",
                                            'pageSize': 1000
                                        }
                                        
                                        if page_token:
                                            request_params['pageToken'] = page_token
                                        
                                        results = self.gdrive.service.files().list(**request_params).execute()
                                        
                                        files = results.get('files', [])
                                        all_files.extend(files)
                                        
                                        page_token = results.get('nextPageToken')
                                        if not page_token:
                                            break
                                    
                                    if all_files:
                                        st.write(f"**Found {len(all_files)} total files (with pagination):**")
                                        
                                        # Show first 10 files and count by type
                                        mime_counts = {}
                                        for file in all_files:
                                            mime_type = file.get('mimeType', 'unknown')
                                            mime_counts[mime_type] = mime_counts.get(mime_type, 0) + 1
                                        
                                        st.write("**File types:**")
                                        for mime_type, count in mime_counts.items():
                                            st.write(f"- {mime_type}: {count} files")
                                        
                                        st.write("**First 10 files:**")
                                        for file in all_files[:10]:
                                            st.write(f"📄 **{file['name']}**")
                                            st.write(f"   - Type: `{file.get('mimeType', 'unknown')}`")
                                            size = int(file.get('size', 0)) if file.get('size') else 0
                                            st.write(f"   - Size: {size/1024:.1f} KB")
                                            st.write("---")
                                        
                                        if len(all_files) > 10:
                                            st.write(f"... and {len(all_files) - 10} more files")
                                    else:
                                        st.write("**Folder is completely empty**")
                                except Exception as e:
                                    st.error(f"Error listing files: {e}")
                else:
                    st.warning("No subfolders found in the main folder")
        
        st.divider()
        
        # Check if already authenticated
        if self.gdrive.load_saved_credentials():
            st.success("✅ Connected to Google Drive")
            
            # Show folder selection
            self._render_folder_selection()
            
            # Disconnect option
            if st.button("🔓 Disconnect Google Drive"):
                # Clear the gdrive object credentials
                self.gdrive.credentials = None
                self.gdrive.service = None
                
                # Clear all persistent storage methods
                if 'gdrive_credentials' in st.session_state:
                    del st.session_state.gdrive_credentials
                if hasattr(st.session_state, '_persistent_gdrive_creds'):
                    del st.session_state._persistent_gdrive_creds
                
                # Clear environment variable
                import os
                if 'GDRIVE_CREDENTIALS' in os.environ:
                    del os.environ['GDRIVE_CREDENTIALS']
                
                # Remove persistent file
                try:
                    if os.path.exists('.gdrive_credentials.json'):
                        os.remove('.gdrive_credentials.json')
                except Exception:
                    pass
                
                st.success("✅ Disconnected from Google Drive")
                st.rerun()
        else:
            self._render_authentication_flow()
    
    def _render_authentication_flow(self):
        """Render Google Drive authentication flow"""
        st.info("📁 Connect your Google Drive to sync SOP documents automatically")
        
        # OAuth client configuration
        with st.expander("🔧 Setup Instructions", expanded=False):
            st.markdown("""
            **To connect Google Drive:**
            1. Go to [Google Cloud Console](https://console.cloud.google.com/)
            2. Create a new project or select existing one
            3. Enable Google Drive API
            4. Create OAuth 2.0 credentials (Desktop application)
            5. Download the JSON file and paste content below
            """)
        
        # Check if client config is in environment variables
        env_client_config = os.getenv('GDRIVE_CLIENT_CONFIG')
        
        if env_client_config:
            st.success("✅ OAuth client configuration found in environment variables")
            try:
                client_config = json.loads(env_client_config)
                if st.button("🔐 Use Environment Configuration"):
                    auth_url, flow = self.gdrive.setup_oauth_flow(client_config)
                    
                    # Store flow in session state
                    st.session_state.oauth_flow = flow
                    st.session_state.client_config = client_config
                    
                    st.success("✅ Configuration loaded!")
                    st.markdown(f"**[Click here to authorize access]({auth_url})**")
                    st.info("Copy the authorization code from the browser and paste it below:")
                    
                    # Also show the URL in case the link doesn't work
                    with st.expander("Having trouble? Copy this URL manually:", expanded=False):
                        st.code(auth_url, language=None)
            except Exception as e:
                st.error(f"Invalid environment configuration: {e}")
        else:
            # Manual client configuration input
            st.info("💡 For persistent authentication, add GDRIVE_CLIENT_CONFIG to environment variables")
            client_config_text = st.text_area(
                "Paste your OAuth 2.0 client configuration (JSON):",
                placeholder='{"installed":{"client_id":"...","client_secret":"...","auth_uri":"...","token_uri":"..."}}',
                height=150
            )
            
            if client_config_text and st.button("🔐 Start Authentication"):
                try:
                    client_config = json.loads(client_config_text)
                    auth_url, flow = self.gdrive.setup_oauth_flow(client_config)
                    
                    # Store flow in session state
                    st.session_state.oauth_flow = flow
                    st.session_state.client_config = client_config
                    
                    st.success("✅ Configuration valid!")
                    st.markdown(f"**[Click here to authorize access]({auth_url})**")
                    st.info("After authorizing, you'll see a code. Copy and paste it below:")
                    
                    # Also show the URL in case the link doesn't work
                    with st.expander("Having trouble? Copy this URL manually:", expanded=False):
                        st.code(auth_url, language=None)
                        
                except json.JSONDecodeError:
                    st.error("❌ Invalid JSON format")
                except Exception as e:
                    st.error(f"❌ Configuration error: {str(e)}")
        
        # Authorization code input
        if 'oauth_flow' in st.session_state:
            auth_code = st.text_input("Enter authorization code:")
            if auth_code and st.button("✅ Complete Authentication"):
                if self.gdrive.authenticate_with_code(st.session_state.oauth_flow, auth_code):
                    st.success("🎉 Successfully connected to Google Drive!")
                    # Clean up session state
                    del st.session_state.oauth_flow
                    st.rerun()
    
    def _render_folder_selection(self):
        """Render folder selection and sync options"""
        st.subheader("📂 Select SOP Folder")
        
        # List folders
        folders = self.gdrive.list_folders()
        if not folders:
            st.warning("No folders found in your Google Drive")
            return
        
        # Folder selection
        folder_options = {f"{folder['name']} ({folder['id']})": folder['id'] for folder in folders}
        selected_folder = st.selectbox(
            "Choose folder containing your SOP documents:",
            options=list(folder_options.keys()),
            key="gdrive_folder_selection"
        )
        
        if selected_folder:
            folder_id = folder_options[selected_folder]
            
            # Show documents in folder
            documents = self.gdrive.list_documents(folder_id)
            if documents:
                st.info(f"📄 Found {len(documents)} documents in this folder")
                
                with st.expander("View Documents", expanded=False):
                    for doc in documents:
                        size_mb = int(doc.get('size', 0)) / (1024 * 1024) if doc.get('size') else 0
                        st.text(f"📄 {doc['name']} ({size_mb:.1f} MB)")
                
                # Sync button
                if st.button("🔄 Sync Documents from Google Drive", type="primary"):
                    with st.spinner("Syncing documents from Google Drive..."):
                        # Sync to local documents folder
                        downloaded_files = self.gdrive.sync_folder(folder_id, "./documents")
                        
                        if downloaded_files:
                            st.success(f"✅ Successfully synced {len(downloaded_files)} documents!")
                            st.info("Documents are now available in your knowledge base with Google Drive links.")
                            
                            # Show synced files with links
                            with st.expander("View Synced Documents", expanded=True):
                                for file_info in downloaded_files:
                                    col1, col2 = st.columns([3, 1])
                                    with col1:
                                        st.text(f"📄 {Path(file_info['path']).name}")
                                    with col2:
                                        st.markdown(f"[Open in Drive]({file_info['gdrive_link']})")
                            
                            # Store folder ID for future syncs
                            st.session_state.gdrive_sync_folder = folder_id
                        else:
                            st.error("❌ No documents were synced")
            else:
                st.warning("No supported documents found in this folder")
                
                # Debug: Show all files in folder
                if st.button("🔍 Debug: Show All Files in Folder"):
                    try:
                        all_files = self.service.files().list(
                            q=f"'{folder_id}' in parents",
                            fields="files(id, name, mimeType, size)"
                        ).execute()
                        
                        files = all_files.get('files', [])
                        if files:
                            st.write(f"**Found {len(files)} total files:**")
                            for file in files:
                                st.write(f"📄 **{file['name']}**")
                                st.write(f"   - Type: `{file.get('mimeType', 'unknown')}`")
                                size = int(file.get('size', 0)) if file.get('size') else 0
                                st.write(f"   - Size: {size/1024:.1f} KB")
                                st.write("---")
                        else:
                            st.write("**Folder is completely empty**")
                    except Exception as e:
                        st.error(f"Error listing files: {e}")
        
        # Auto-sync option
        if 'gdrive_sync_folder' in st.session_state:
            st.divider()
            if st.button("🔄 Re-sync Documents"):
                folder_id = st.session_state.gdrive_sync_folder
                with st.spinner("Re-syncing documents..."):
                    downloaded_files = self.gdrive.sync_folder(folder_id, "./documents")
                    if downloaded_files:
                        st.success(f"✅ Re-synced {len(downloaded_files)} documents!")
                        
                        # Show synced files with links
                        with st.expander("View Re-synced Documents", expanded=True):
                            for file_info in downloaded_files:
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    st.text(f"📄 {Path(file_info['path']).name}")
                                with col2:
                                    st.markdown(f"[Open in Drive]({file_info['gdrive_link']})")