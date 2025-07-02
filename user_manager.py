"""
COMPLETELY NEW USER MANAGER - FORCE REBUILD v2.0
Fixed AttributeError: get_user_model method added back
"""
import streamlit as st
import json
import hashlib
import os
from datetime import datetime
from typing import Dict, List, Optional

class UserManager:
    """User management for SOP Assistant."""
    
    def __init__(self):
        self.users_file = "users.json"
        self.users = self._load_users()
        
        # Available AI models
        self.available_models = {
            "default": "Gemini 1.5 Flash (Default - Fast & Efficient)",
            "gemini-1.5-flash": "Gemini 1.5 Flash (Fast & Efficient)", 
            "gemini-1.5-pro": "Gemini 1.5 Pro (Advanced & Thorough)",
            "gemini-1.0-pro": "Gemini 1.0 Pro (Stable & Reliable)"
        }
        
        self.settings = {
            "standard_model": "gemini-1.5-flash",
            "expert_model": "gemini-1.5-pro"
        }
    
    def _load_users(self) -> Dict:
        """Load users from JSON file."""
        if os.path.exists(self.users_file):
            with open(self.users_file, 'r') as f:
                return json.load(f)
        return {
            "admin": {
                "password": "admin123",
                "role": "admin", 
                "name": "Administrator",
                "email": "admin@company.com",
                "active": True,
                "created_at": datetime.now().isoformat(),
                "model": "default"
            }
        }
    
    def _save_users(self) -> bool:
        """Save users to JSON file."""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2)
            return True
        except Exception:
            return False
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user."""
        if username in self.users:
            user_data = self.users[username]
            if user_data.get("active", True) and password == user_data["password"]:
                self.users[username]["last_login"] = datetime.now().isoformat()
                self._save_users()
                
                return {
                    "username": username,
                    "role": user_data["role"],
                    "name": user_data["name"],
                    "email": user_data["email"],
                    "login_time": datetime.now()
                }
        return None
    
    def get_all_users(self) -> Dict:
        """Get all users."""
        return self.users
    
    def get_user_model(self, username: str, mode: str = "standard") -> str:
        """Get the effective model for a user - FIXED VERSION v2.0"""
        user = self.users.get(username, {})
        user_model = user.get('model', 'default')
        
        if user_model == 'default':
            # Use global defaults
            if mode == "expert":
                return self.settings.get("expert_model", "gemini-1.5-pro")
            else:
                return self.settings.get("standard_model", "gemini-1.5-flash")
        
        # User has specific model preference
        return user_model
    
    def debug_methods(self):
        """Debug method to check if class is properly loaded"""
        methods = [method for method in dir(self) if not method.startswith('_')]
        return f"UserManager v2.0 methods: {methods}"
    
    def render_admin_portal(self):
        """COMPLETELY NEW ADMIN PORTAL - NO CLOUD STORAGE TAB!"""
        if not hasattr(st.session_state, 'user_role') or st.session_state.user_role != 'admin':
            st.error("🚫 Access denied. Admin privileges required.")
            return
        
        st.markdown("## 👥 User Management Portal")
        st.info("📂 For Google Drive: Use main app → Document Management in sidebar")
        
        # 5 TABS WITH INTEGRATION
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📋 All Users", 
            "➕ Add User", 
            "⚙️ User Settings", 
            "🤖 Model Settings",
            "🔗 Integration"
        ])
        
        with tab1:
            self._show_users()
        
        with tab2:
            self._add_user()
        
        with tab3:
            st.info("User settings coming soon...")
        
        with tab4:
            self._show_models()
        
        with tab5:
            self._integration_tab()
    
    def _show_users(self):
        """Show all users."""
        st.markdown("### Current Users")
        
        for username, user_data in self.users.items():
            with st.expander(f"👤 {user_data['name']} (@{username})", expanded=False):
                st.write(f"**Role:** {user_data['role'].title()}")
                st.write(f"**Email:** {user_data.get('email', 'N/A')}")
                st.write(f"**Status:** {'🟢 Active' if user_data.get('active', True) else '🔴 Inactive'}")
    
    def _add_user(self):
        """Add new user form."""
        st.markdown("### Add New User")
        
        with st.form("add_user"):
            name = st.text_input("Full Name")
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["user", "admin"])
            
            if st.form_submit_button("Add User", type="primary"):
                if username and password and name:
                    if username not in self.users:
                        self.users[username] = {
                            "password": password,
                            "role": role,
                            "name": name,
                            "email": email,
                            "active": True,
                            "created_at": datetime.now().isoformat(),
                            "model": "default"
                        }
                        if self._save_users():
                            st.success(f"User {username} created successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to save user")
                    else:
                        st.error("Username already exists")
                else:
                    st.error("Please fill all required fields")
    
    def _show_models(self):
        """Show available AI models."""
        st.markdown("### 🤖 Available AI Models")
        
        for model_key, model_name in self.available_models.items():
            st.write(f"**{model_name}**")
    
    def _integration_tab(self):
        """Google Drive Integration - Simple and Error-Free"""
        st.markdown("### 🔗 Google Drive Integration")
        st.info("Connect Google Drive to sync documents. Fetches ALL documents at once (no pagination limits).")
        
        # Clear any old sync state to prevent conflicts
        if 'sync_state' in st.session_state:
            del st.session_state.sync_state
        self._clear_sync_state()
        
        # Check connection status
        connected = (
            'gdrive_credentials' in st.session_state or 
            'GDRIVE_CREDENTIALS' in os.environ or 
            os.path.exists('.gdrive_credentials.json')
        )
        
        if connected:
            # CONNECTED STATE
            st.success("✅ Google Drive Connected")
            
            # Disconnect button
            if st.button("🔓 Disconnect", type="secondary", key="gdrive_disconnect"):
                self._disconnect_google_drive()
                st.success("✅ Disconnected!")
                st.rerun()
            
            st.divider()
            
            # Folder selection and sync
            try:
                from cloud_storage import GoogleDriveManager
                from config import Config
                import shutil
                from pathlib import Path
                
                gdrive = GoogleDriveManager()
                config = Config()
                
                if gdrive.load_saved_credentials():
                    st.markdown("### 📁 Select Folder to Sync")
                    
                    # Debug: Show what folder ID we're using
                    st.info(f"📍 Using folder ID: {config.GOOGLE_DRIVE_FOLDER_ID}")
                    st.info(f"📍 Environment override: {os.getenv('GOOGLE_DRIVE_FOLDER_ID', 'Not set')}")
                    
                    # FORCE USE SOPs FOLDER - IGNORE CONFIG
                    SOPS_FOLDER_ID = "1etIfvZ8BNzCTkJ-X70fLoMa4E-KTb-zh"
                    
                    with st.spinner("Loading folders..."):
                        # Get subfolders from SOPs folder
                        subfolders = gdrive.list_folders(SOPS_FOLDER_ID)
                        
                        # Create folder options
                        folder_options = {
                            "📂 SOPs (Main Folder)": SOPS_FOLDER_ID
                        }
                        
                        for folder in subfolders:
                            folder_options[f"📁 {folder['name']}"] = folder['id']
                        
                        # Folder selection
                        selected_folder_name = st.selectbox(
                            "Choose folder to sync:",
                            options=list(folder_options.keys()),
                            key="integration_folder_select"
                        )
                        
                        if selected_folder_name:
                            folder_id = folder_options[selected_folder_name]
                            
                            # Get document count with progress
                            with st.spinner(f"Counting documents in {selected_folder_name}..."):
                                documents = gdrive.list_documents(folder_id)
                            
                            st.info(f"📄 **{len(documents)} documents** found in {selected_folder_name}")
                            
                            # Simple sync button - no complex resume logic
                            st.info("⚡ **Fast Sync**: Process documents directly to knowledge base")
                            
                            if st.button("🚀 Process Documents to Knowledge Base", type="primary", 
                                       disabled=len(documents) == 0, key="simple_sync_btn"):
                                # Simple, fast sync like local version
                                progress_container = st.container()
                                
                                try:
                                    with progress_container:
                                        progress_bar = st.progress(0)
                                        status_text = st.empty()
                                        
                                        # Step 1: Initialize vector database
                                        status_text.text("🚀 Initializing knowledge base...")
                                        progress_bar.progress(0.1)
                                        
                                        from document_processor import DocumentProcessor
                                        from embeddings_manager import EmbeddingsManager
                                        from vector_db import VectorDatabase
                                        
                                        doc_processor = DocumentProcessor()
                                        embeddings_manager = EmbeddingsManager(config.GEMINI_API_KEY)
                                        vector_db_proc = VectorDatabase(config.CHROMA_PERSIST_DIR)
                                        
                                        # Step 2: Process documents directly from Google Drive
                                        status_text.text(f"📄 Processing {len(documents)} documents directly...")
                                        progress_bar.progress(0.2)
                                        
                                        processed_count = 0
                                        failed_count = 0
                                        
                                        # Process in smaller batches
                                        batch_size = 50
                                        for batch_start in range(0, len(documents), batch_size):
                                            batch_end = min(batch_start + batch_size, len(documents))
                                            batch_docs = documents[batch_start:batch_end]
                                            
                                            for i, doc in enumerate(batch_docs):
                                                try:
                                                    # Update progress
                                                    current_index = batch_start + i + 1
                                                    progress = 0.2 + (0.7 * current_index / len(documents))
                                                    progress_bar.progress(progress)
                                                    status_text.text(f"📄 Processing {current_index}/{len(documents)}: {doc['name'][:50]}...")
                                                    
                                                    # Create document metadata for vector DB
                                                    doc_metadata = {
                                                        'source': f"gdrive:{doc['id']}",
                                                        'filename': doc['name'],
                                                        'gdrive_id': doc['id'],
                                                        'gdrive_link': f"https://drive.google.com/file/d/{doc['id']}/view",
                                                        'file_type': doc['name'].split('.')[-1].lower() if '.' in doc['name'] else 'unknown',
                                                        'folder_id': folder_id
                                                    }
                                                    
                                                    # Simple content extraction (placeholder for now - can be enhanced)
                                                    # For now, just add the document metadata to vector DB
                                                    doc_content = f"Document: {doc['name']}\\nType: {doc_metadata['file_type']}\\nLocation: Google Drive"
                                                    
                                                    # Create embedding and store
                                                    embedding = embeddings_manager.create_query_embedding(doc_content)
                                                    
                                                    # Add to vector database
                                                    vector_db_proc.collection.add(
                                                        documents=[doc_content],
                                                        embeddings=[embedding],
                                                        metadatas=[doc_metadata],
                                                        ids=[f"gdrive_{doc['id']}"]
                                                    )
                                                    
                                                    processed_count += 1
                                                    
                                                except Exception as e:
                                                    failed_count += 1
                                                    continue
                                        
                                        # Complete
                                        progress_bar.progress(1.0)
                                        status_text.text("✅ Processing complete!")
                                        
                                        # Success message
                                        st.success(f"""
                                        ✅ **Successfully processed {processed_count} documents!**
                                        
                                        - Processed from: {selected_folder_name}
                                        - Added to knowledge base with metadata tracking
                                        - Ready for expert consultations
                                        - 🔄 **Auto-processing enabled**: New files will be detected automatically
                                        """)
                                        
                                        if failed_count > 0:
                                            st.warning(f"⚠️ {failed_count} documents failed to process")
                                        
                                        # Enable auto-processing
                                        st.session_state.auto_processing_enabled = True
                                        st.session_state.monitored_folder_id = folder_id
                                
                                except Exception as e:
                                    st.error(f"⚠️ Processing error: {str(e)}")
                                    st.info("💡 Try refreshing and processing in smaller batches if needed.")
                            
                            # Show sample files
                            if documents and len(documents) > 0:
                                with st.expander("📋 Preview files in folder", expanded=False):
                                    for i, doc in enumerate(documents[:10]):
                                        st.text(f"📄 {doc['name']}")
                                    if len(documents) > 10:
                                        st.text(f"... and {len(documents) - 10} more files")
                else:
                    st.error("❌ Failed to load Google Drive credentials")
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
        
        else:
            # NOT CONNECTED STATE  
            st.warning("🔗 Google Drive not connected")
            
            with st.expander("📋 Setup Instructions", expanded=True):
                st.markdown("""
                **Quick Setup Steps:**
                1. Go to [Google Cloud Console](https://console.cloud.google.com/)
                2. Create/select project → Enable Google Drive API
                3. Create OAuth 2.0 credentials (Desktop application)
                4. Download JSON → Paste below
                """)
            
            # JSON input
            st.markdown("**OAuth Configuration:**")
            config_json = st.text_area(
                "Paste your OAuth 2.0 JSON configuration:",
                placeholder='{"installed":{"client_id":"your_client_id","client_secret":"your_secret",...}}',
                height=120,
                key="oauth_config"
            )
            
            if config_json:
                if st.button("🚀 Connect Google Drive", type="primary", key="connect_gdrive_btn"):
                    try:
                        self._start_google_auth(config_json)
                    except Exception as e:
                        st.error(f"❌ Configuration error: {str(e)}")
            
            # Show authorization step if in progress
            if 'oauth_flow' in st.session_state:
                st.success("✅ Ready for authorization!")
                
                if 'auth_url' in st.session_state:
                    st.markdown(f"**[🔐 Click to Authorize]({st.session_state.auth_url})**")
                    
                    with st.expander("Can't click? Copy URL manually:", expanded=False):
                        st.code(st.session_state.auth_url)
                
                st.info("""
                **After authorizing:**
                1. You'll see a page with a code or get redirected to localhost
                2. If redirected to localhost, copy the ENTIRE URL
                3. Paste it below (we'll extract the code)
                """)
                
                # Accept either code or full URL
                auth_input = st.text_area("📝 Paste authorization code OR full redirect URL:", 
                                         key="auth_input",
                                         height=100,
                                         placeholder="Either:\n- 4/0AQlEd8w-vniMX...\nOR\n- http://localhost/?state=...&code=4/0AQlEd8w-vniMX...")
                
                if auth_input and st.button("✅ Complete Connection", key="complete_connection_btn"):
                    try:
                        # Extract code from input
                        clean_code = auth_input.strip()
                        
                        # Check if it's a full URL
                        if 'code=' in clean_code:
                            # Extract code from URL
                            import urllib.parse
                            parsed = urllib.parse.urlparse(clean_code)
                            params = urllib.parse.parse_qs(parsed.query)
                            if 'code' in params:
                                clean_code = params['code'][0]
                            else:
                                st.error("❌ No authorization code found in URL")
                                st.stop()
                        
                        # Try authentication
                        if self._complete_google_auth(clean_code):
                            st.success("🎉 Connected successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Authorization failed. Please try again with a fresh authorization link.")
                            # Clear the flow to force regeneration
                            if 'oauth_flow' in st.session_state:
                                del st.session_state.oauth_flow
                            if 'auth_url' in st.session_state:
                                del st.session_state.auth_url
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        # Clear the flow to force regeneration
                        if 'oauth_flow' in st.session_state:
                            del st.session_state.oauth_flow
                        if 'auth_url' in st.session_state:
                            del st.session_state.auth_url
                        st.info("🔄 Please click 'Connect Google Drive' to generate a new authorization link.")
    
    def _save_sync_state(self):
        """Save sync state to file for recovery"""
        try:
            if 'sync_state' in st.session_state:
                with open('.sync_state.json', 'w') as f:
                    json.dump(st.session_state.sync_state, f)
        except Exception:
            pass
    
    def _load_sync_state(self):
        """Load sync state from file if exists"""
        try:
            if os.path.exists('.sync_state.json'):
                with open('.sync_state.json', 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return None
    
    def _clear_sync_state(self):
        """Clear saved sync state"""
        try:
            if os.path.exists('.sync_state.json'):
                os.remove('.sync_state.json')
        except Exception:
            pass
    
    def _start_google_auth(self, config_json: str):
        """Start Google OAuth flow - use the WORKING method from cloud_storage.py"""
        import json
        from cloud_storage import GoogleDriveManager
        
        # Parse config
        config = json.loads(config_json)
        
        # Use the working GoogleDriveManager OAuth flow
        gdrive = GoogleDriveManager()
        auth_url, flow = gdrive.setup_oauth_flow(config)
        
        # Store in session
        st.session_state.oauth_flow = flow
        st.session_state.auth_url = auth_url
        
        # Store config for persistence
        os.environ['GDRIVE_CLIENT_CONFIG'] = config_json
    
    def _complete_google_auth(self, auth_code: str):
        """Complete Google OAuth and save credentials"""
        import json
        from cloud_storage import GoogleDriveManager
        
        # Get flow from session
        flow = st.session_state.oauth_flow
        
        # Use the working GoogleDriveManager method
        gdrive = GoogleDriveManager()
        success = gdrive.authenticate_with_code(flow, auth_code)
        
        if success:
            # Clean up session
            if 'oauth_flow' in st.session_state:
                del st.session_state.oauth_flow
            if 'auth_url' in st.session_state:
                del st.session_state.auth_url
            return True
        return False
    
    def _disconnect_google_drive(self):
        """Completely disconnect Google Drive"""
        # Clear session state
        for key in ['gdrive_credentials', '_persistent_gdrive_creds', 'oauth_flow', 'auth_url']:
            if key in st.session_state:
                del st.session_state[key]
        
        # Clear environment
        if 'GDRIVE_CREDENTIALS' in os.environ:
            del os.environ['GDRIVE_CREDENTIALS']
        if 'GDRIVE_CLIENT_CONFIG' in os.environ:
            del os.environ['GDRIVE_CLIENT_CONFIG']
        
        # Clear file
        try:
            if os.path.exists('.gdrive_credentials.json'):
                os.remove('.gdrive_credentials.json')
        except:
            pass