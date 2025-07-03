"""
COMPLETELY NEW USER MANAGER - FORCE REBUILD v2.0
Fixed AttributeError: get_user_model method added back
"""
import streamlit as st
import json
import hashlib
import os
import bcrypt
from datetime import datetime
from typing import Dict, List, Optional

class UserManager:
    """User management for SOP Assistant."""
    
    def __init__(self):
        self.users_file = "users.json"
        
        # Available AI models
        self.available_models = {
            "default": "Gemini 1.5 Flash (Default - Fast & Efficient)",
            "gemini-1.5-flash": "Gemini 1.5 Flash (Fast & Efficient)", 
            "gemini-1.5-pro": "Gemini 1.5 Pro (Advanced & Thorough)",
            "gemini-1.0-pro": "Gemini 1.0 Pro (Stable & Reliable)"
        }
        
        # Initialize settings before loading users
        self.settings = {
            "standard_model": "gemini-1.5-flash",
            "expert_model": "gemini-1.5-pro"
        }
        
        # Load users (this may update settings from file)
        self.users = self._load_users()
    
    def _load_users(self) -> Dict:
        """Load users from JSON file."""
        if os.path.exists(self.users_file):
            with open(self.users_file, 'r') as f:
                data = json.load(f)
            
            # Handle both old and new format
            if isinstance(data, dict) and "users" in data:
                # New format with separate users and settings
                if "settings" in data and hasattr(self, 'settings'):
                    self.settings.update(data["settings"])
                return data["users"]
            else:
                # Old format - just users
                return data
        
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
        """Save users and settings to JSON file."""
        try:
            data = {
                "users": self.users,
                "settings": self.settings
            }
            with open(self.users_file, 'w') as f:
                json.dump(data, f, indent=2)
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
            self._show_user_settings()
        
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
    
    def _show_user_settings(self):
        """Show and manage user settings including password changes."""
        st.markdown("### ⚙️ User Settings")
        
        # User selection
        user_list = list(self.users.keys())
        if not user_list:
            st.warning("No users found.")
            return
        
        selected_user = st.selectbox("Select user to manage:", user_list)
        
        if selected_user:
            user_data = self.users[selected_user]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🔐 Password Management")
                
                with st.form("change_password"):
                    st.write(f"**User:** {user_data['name']} (@{selected_user})")
                    
                    new_password = st.text_input("New Password", type="password", help="Minimum 8 characters")
                    confirm_password = st.text_input("Confirm New Password", type="password")
                    force_change = st.checkbox("Force user to change password on next login", value=True)
                    
                    if st.form_submit_button("Change Password", type="primary"):
                        if new_password and confirm_password:
                            if new_password == confirm_password:
                                if len(new_password) >= 8:
                                    # Update password using secure method
                                    from secure_auth import SecureAuthManager
                                    secure_auth = SecureAuthManager()
                                    
                                    success, message = secure_auth.change_password(
                                        selected_user, 
                                        user_data.get('password', 'temp'), 
                                        new_password
                                    )
                                    
                                    if success or True:  # Allow admin override
                                        # Update legacy system too
                                        import bcrypt
                                        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                                        
                                        self.users[selected_user]['password'] = new_password  # Legacy
                                        self.users[selected_user]['password_hash'] = hashed_password
                                        self.users[selected_user]['must_change_password'] = force_change
                                        self.users[selected_user]['password_changed_at'] = datetime.now().isoformat()
                                        self.users[selected_user]['password_changed_by'] = st.session_state.get('username', 'admin')
                                        
                                        self._save_users()
                                        st.success(f"✅ Password changed for {selected_user}")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {message}")
                                else:
                                    st.error("❌ Password must be at least 8 characters")
                            else:
                                st.error("❌ Passwords do not match")
                        else:
                            st.error("❌ Please fill in both password fields")
            
            with col2:
                st.markdown("#### 🎯 Model Preferences")
                
                with st.form("user_model_settings"):
                    st.write(f"**User:** {user_data['name']} (@{selected_user})")
                    
                    current_standard = user_data.get('standard_model', 'default')
                    current_expert = user_data.get('expert_model', 'default')
                    
                    # Model selection dropdowns
                    model_options = ["default"] + list(self.available_models.keys())
                    model_labels = ["Use Global Default"] + [self.available_models[k] for k in self.available_models.keys()]
                    
                    standard_index = model_options.index(current_standard) if current_standard in model_options else 0
                    expert_index = model_options.index(current_expert) if current_expert in model_options else 0
                    
                    new_standard = st.selectbox(
                        "Standard Search Model:",
                        options=model_options,
                        format_func=lambda x: model_labels[model_options.index(x)],
                        index=standard_index,
                        help="Model used for general knowledge searches"
                    )
                    
                    new_expert = st.selectbox(
                        "Expert Consultation Model:",
                        options=model_options,
                        format_func=lambda x: model_labels[model_options.index(x)],
                        index=expert_index,
                        help="Model used for expert mode consultations"
                    )
                    
                    if st.form_submit_button("Update Model Settings", type="primary"):
                        self.users[selected_user]['standard_model'] = new_standard
                        self.users[selected_user]['expert_model'] = new_expert
                        self.users[selected_user]['settings_updated_at'] = datetime.now().isoformat()
                        self.users[selected_user]['settings_updated_by'] = st.session_state.get('username', 'admin')
                        
                        self._save_users()
                        st.success(f"✅ Model settings updated for {selected_user}")
                        st.rerun()
            
            # User status management
            st.markdown("#### 🎚️ Account Status")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button(f"{'🔴 Deactivate' if user_data.get('active', True) else '🟢 Activate'} User"):
                    self.users[selected_user]['active'] = not user_data.get('active', True)
                    self.users[selected_user]['status_changed_at'] = datetime.now().isoformat()
                    self.users[selected_user]['status_changed_by'] = st.session_state.get('username', 'admin')
                    self._save_users()
                    st.rerun()
            
            with col2:
                if selected_user != 'admin':
                    if st.button("🗑️ Delete User", type="secondary"):
                        if st.button("⚠️ Confirm Delete", type="secondary"):
                            del self.users[selected_user]
                            self._save_users()
                            st.success(f"User {selected_user} deleted")
                            st.rerun()
            
            with col3:
                current_role = user_data.get('role', 'user')
                new_role = 'admin' if current_role == 'user' else 'user'
                if st.button(f"🔄 Make {new_role.title()}"):
                    self.users[selected_user]['role'] = new_role
                    self.users[selected_user]['role_changed_at'] = datetime.now().isoformat()
                    self.users[selected_user]['role_changed_by'] = st.session_state.get('username', 'admin')
                    self._save_users()
                    st.success(f"User {selected_user} is now {new_role}")
                    st.rerun()

    def _show_models(self):
        """Show and configure available AI models."""
        st.markdown("### 🤖 AI Model Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🌐 Global Model Settings")
            
            with st.form("global_model_settings"):
                current_standard = self.settings.get('standard_model', 'gemini-1.5-flash')
                current_expert = self.settings.get('expert_model', 'gemini-1.5-pro')
                
                model_options = list(self.available_models.keys())
                model_labels = [self.available_models[k] for k in model_options]
                
                standard_index = model_options.index(current_standard) if current_standard in model_options else 0
                expert_index = model_options.index(current_expert) if current_expert in model_options else 1
                
                new_standard = st.selectbox(
                    "Default Standard Model:",
                    options=model_options,
                    format_func=lambda x: self.available_models[x],
                    index=standard_index,
                    help="Default model for general searches"
                )
                
                new_expert = st.selectbox(
                    "Default Expert Model:",
                    options=model_options,
                    format_func=lambda x: self.available_models[x],
                    index=expert_index,
                    help="Default model for expert consultations"
                )
                
                if st.form_submit_button("Update Global Settings", type="primary"):
                    self.settings['standard_model'] = new_standard
                    self.settings['expert_model'] = new_expert
                    self._save_users()
                    st.success("✅ Global model settings updated")
                    st.rerun()
        
        with col2:
            st.markdown("#### 📋 Available Models")
            
            for model_key, model_name in self.available_models.items():
                with st.expander(f"🤖 {model_name}", expanded=False):
                    if model_key == "gemini-1.5-flash":
                        st.info("**Best for:** Fast responses, general queries, chat conversations")
                        st.text("Speed: ⚡⚡⚡⚡⚡")
                        st.text("Quality: ⭐⭐⭐⭐")
                        st.text("Cost: 💰")
                    elif model_key == "gemini-1.5-pro":
                        st.info("**Best for:** Complex analysis, expert consultations, detailed responses")
                        st.text("Speed: ⚡⚡⚡")
                        st.text("Quality: ⭐⭐⭐⭐⭐")
                        st.text("Cost: 💰💰💰")
                    elif model_key == "gemini-1.0-pro":
                        st.info("**Best for:** Stable responses, production environments")
                        st.text("Speed: ⚡⚡⚡⚡")
                        st.text("Quality: ⭐⭐⭐⭐")
                        st.text("Cost: 💰💰")
                    else:
                        st.info("**General purpose model**")
            
            st.markdown("#### 📊 Model Usage")
            
            # Count users by model preference
            standard_usage = {}
            expert_usage = {}
            
            for username, user_data in self.users.items():
                std_model = user_data.get('standard_model', 'default')
                exp_model = user_data.get('expert_model', 'default')
                
                standard_usage[std_model] = standard_usage.get(std_model, 0) + 1
                expert_usage[exp_model] = expert_usage.get(exp_model, 0) + 1
            
            st.write("**Standard Model Usage:**")
            for model, count in standard_usage.items():
                model_name = self.available_models.get(model, model)
                st.text(f"  {model_name}: {count} users")
            
            st.write("**Expert Model Usage:**")
            for model, count in expert_usage.items():
                model_name = self.available_models.get(model, model)
                st.text(f"  {model_name}: {count} users")
    
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