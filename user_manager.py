"""
User Management System for SOP Assistant
Provides admin functionality to manage users
"""

import streamlit as st
import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

class UserManager:
    """Handles user management for admin users."""
    
    def __init__(self, users_file: str = "users.json", settings_file: str = "app_settings.json"):
        self.users_file = users_file
        self.settings_file = settings_file
        self.users = self._load_users()
        self.settings = self._load_settings()
        
        # Available Gemini models
        self.available_models = {
            "gemini-1.5-flash": "Gemini 1.5 Flash (Fast, Cost-effective)",
            "gemini-1.5-pro": "Gemini 1.5 Pro (Most capable, Higher cost)",
            "gemini-1.0-pro": "Gemini 1.0 Pro (Stable, Balanced)",
            "default": "System Default (Uses config.py setting)"
        }
    
    def _load_users(self) -> Dict:
        """Load users from JSON file or create default users."""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Default users if file doesn't exist
        return {
            "admin": {
                "password": "admin123",
                "role": "admin",
                "name": "Administrator",
                "email": "admin@company.com",
                "created_at": datetime.now().isoformat(),
                "last_login": None,
                "active": True
            },
            "user": {
                "password": "user123",
                "role": "user",
                "name": "User",
                "email": "user@company.com",
                "created_at": datetime.now().isoformat(),
                "last_login": None,
                "active": True
            }
        }
    
    def _save_users(self):
        """Save users to JSON file."""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2)
            return True
        except Exception as e:
            st.error(f"Failed to save users: {e}")
            return False
    
    def _load_settings(self) -> Dict:
        """Load application settings."""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Default settings
        return {
            "default_model": "gemini-1.5-flash",
            "expert_model": "gemini-1.5-pro"
        }
    
    def _save_settings(self):
        """Save application settings."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            return True
        except Exception as e:
            st.error(f"Failed to save settings: {e}")
            return False
    
    def add_user(self, username: str, password: str, name: str, email: str, role: str = "user", model: str = "default") -> bool:
        """Add a new user."""
        if username in self.users:
            return False
        
        self.users[username] = {
            "password": password,
            "role": role,
            "name": name,
            "email": email,
            "model": model,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "active": True
        }
        
        return self._save_users()
    
    def update_user(self, username: str, **kwargs) -> bool:
        """Update user information."""
        if username not in self.users:
            return False
        
        for key, value in kwargs.items():
            if key in ["password", "role", "name", "email", "active", "model"]:
                self.users[username][key] = value
        
        self.users[username]["updated_at"] = datetime.now().isoformat()
        return self._save_users()
    
    def delete_user(self, username: str) -> bool:
        """Delete a user (cannot delete admin)."""
        if username == "admin" or username not in self.users:
            return False
        
        del self.users[username]
        return self._save_users()
    
    def get_user(self, username: str) -> Optional[Dict]:
        """Get user information."""
        return self.users.get(username)
    
    def get_all_users(self) -> Dict:
        """Get all users."""
        return self.users
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user."""
        if username in self.users:
            user_data = self.users[username]
            if user_data.get("active", True) and password == user_data["password"]:
                # Update last login
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
    
    def get_user_model(self, username: str, mode: str = "standard") -> str:
        """Get the effective model for a user."""
        user = self.users.get(username, {})
        user_model = user.get('model', 'default')
        
        if user_model == 'default':
            # Use global defaults
            if mode == "expert":
                return self.settings.get("expert_model", "gemini-1.5-pro")
            else:
                return self.settings.get("default_model", "gemini-1.5-flash")
        else:
            return user_model
    
    def render_admin_portal(self):
        """Render the admin user management portal."""
        if not hasattr(st.session_state, 'user_role') or st.session_state.user_role != 'admin':
            st.error("🚫 Access denied. Admin privileges required.")
            return
        
        st.markdown("## 👥 User Management Portal")
        
        # Tabs for different admin functions
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 All Users", "➕ Add User", "⚙️ User Settings", "🤖 Model Settings", "☁️ Cloud Storage"])
        
        with tab1:
            self._render_users_list()
        
        with tab2:
            self._render_add_user()
        
        with tab3:
            self._render_user_settings()
        
        with tab4:
            self._render_model_settings()
            
        with tab5:
            self._render_cloud_storage()
    
    def _render_users_list(self):
        """Render list of all users."""
        st.markdown("### Current Users")
        
        users = self.get_all_users()
        if not users:
            st.info("No users found.")
            return
        
        for username, user_data in users.items():
            with st.expander(f"👤 {user_data['name']} (@{username})", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Role:** {user_data['role'].title()}")
                    st.write(f"**Email:** {user_data.get('email', 'N/A')}")
                    st.write(f"**Status:** {'🟢 Active' if user_data.get('active', True) else '🔴 Inactive'}")
                    model = user_data.get('model', 'default')
                    model_display = self.available_models.get(model, model).split(' (')[0]
                    st.write(f"**AI Model:** {model_display}")
                
                with col2:
                    st.write(f"**Created:** {user_data.get('created_at', 'N/A')[:10]}")
                    last_login = user_data.get('last_login')
                    if last_login:
                        st.write(f"**Last Login:** {last_login[:10]}")
                    else:
                        st.write("**Last Login:** Never")
                
                # Action buttons
                col_edit, col_delete, col_toggle = st.columns(3)
                
                with col_edit:
                    if st.button(f"✏️ Edit", key=f"edit_{username}"):
                        st.session_state[f"editing_{username}"] = True
                
                with col_delete:
                    if username != "admin":  # Cannot delete admin
                        if st.button(f"🗑️ Delete", key=f"delete_{username}"):
                            if self.delete_user(username):
                                st.success(f"User {username} deleted!")
                                st.rerun()
                            else:
                                st.error("Failed to delete user")
                
                with col_toggle:
                    current_status = user_data.get('active', True)
                    new_status = not current_status
                    status_text = "🔴 Deactivate" if current_status else "🟢 Activate"
                    
                    if st.button(status_text, key=f"toggle_{username}"):
                        if self.update_user(username, active=new_status):
                            st.success(f"User {username} {'activated' if new_status else 'deactivated'}!")
                            st.rerun()
                
                # Edit form (if editing)
                if st.session_state.get(f"editing_{username}", False):
                    st.markdown("---")
                    with st.form(f"edit_form_{username}"):
                        new_name = st.text_input("Name", value=user_data['name'])
                        new_email = st.text_input("Email", value=user_data.get('email', ''))
                        new_role = st.selectbox("Role", ["user", "admin"], 
                                              index=0 if user_data['role'] == 'user' else 1)
                        
                        current_model = user_data.get('model', 'default')
                        model_options = list(self.available_models.keys())
                        model_index = model_options.index(current_model) if current_model in model_options else 0
                        new_model = st.selectbox("AI Model", options=model_options,
                                               format_func=lambda x: self.available_models[x],
                                               index=model_index)
                        
                        new_password = st.text_input("New Password (leave blank to keep current)", 
                                                   type="password")
                        
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.form_submit_button("💾 Save Changes", type="primary"):
                                updates = {"name": new_name, "email": new_email, "role": new_role, "model": new_model}
                                if new_password:
                                    updates["password"] = new_password
                                
                                if self.update_user(username, **updates):
                                    st.success("User updated successfully!")
                                    del st.session_state[f"editing_{username}"]
                                    st.rerun()
                                else:
                                    st.error("Failed to update user")
                        
                        with col_cancel:
                            if st.form_submit_button("❌ Cancel"):
                                del st.session_state[f"editing_{username}"]
                                st.rerun()
    
    def _render_add_user(self):
        """Render add user form."""
        st.markdown("### Add New User")
        
        with st.form("add_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                username = st.text_input("Username*", placeholder="Enter username")
                name = st.text_input("Full Name*", placeholder="Enter full name")
                password = st.text_input("Password*", type="password", placeholder="Enter password")
            
            with col2:
                email = st.text_input("Email", placeholder="user@company.com")
                role = st.selectbox("Role", ["user", "admin"])
                model = st.selectbox("AI Model", options=list(self.available_models.keys()),
                                   format_func=lambda x: self.available_models[x],
                                   index=list(self.available_models.keys()).index("default"))
                confirm_password = st.text_input("Confirm Password*", type="password", 
                                               placeholder="Confirm password")
            
            if st.form_submit_button("➕ Add User", type="primary"):
                # Validation
                if not username or not name or not password:
                    st.error("⚠️ Username, name, and password are required!")
                elif password != confirm_password:
                    st.error("⚠️ Passwords do not match!")
                elif username in self.users:
                    st.error(f"⚠️ Username '{username}' already exists!")
                elif len(password) < 6:
                    st.error("⚠️ Password must be at least 6 characters!")
                else:
                    if self.add_user(username, password, name, email, role, model):
                        st.success(f"✅ User '{username}' added successfully!")
                        st.balloons()
                    else:
                        st.error("❌ Failed to add user!")
    
    def _render_user_settings(self):
        """Render user settings and system configuration."""
        st.markdown("### System Settings")
        
        # User statistics
        users = self.get_all_users()
        total_users = len(users)
        active_users = sum(1 for u in users.values() if u.get('active', True))
        admin_users = sum(1 for u in users.values() if u['role'] == 'admin')
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Users", total_users)
        with col2:
            st.metric("Active Users", active_users)
        with col3:
            st.metric("Admin Users", admin_users)
        
        st.markdown("---")
        
        # Export/Import users
        st.markdown("### 📤 Export/Import Users")
        
        col_export, col_import = st.columns(2)
        
        with col_export:
            if st.button("📋 Export Users (JSON)"):
                users_json = json.dumps(users, indent=2)
                st.download_button(
                    label="💾 Download users.json",
                    data=users_json,
                    file_name="users_backup.json",
                    mime="application/json"
                )
        
        with col_import:
            uploaded_file = st.file_uploader("📁 Import Users", type=['json'])
            if uploaded_file is not None:
                try:
                    imported_users = json.load(uploaded_file)
                    if st.button("🔄 Import Users"):
                        self.users.update(imported_users)
                        if self._save_users():
                            st.success("Users imported successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to import users!")
                except Exception as e:
                    st.error(f"Invalid JSON file: {e}")
    
    def _render_model_settings(self):
        """Render AI model settings."""
        st.markdown("### 🤖 AI Model Configuration")
        
        # Global model settings
        st.markdown("#### Global Default Models")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Standard Mode (Knowledge Search)")
            current_default = self.settings.get("default_model", "gemini-1.5-flash")
            default_model = st.selectbox(
                "Default Model for Knowledge Search",
                options=list(self.available_models.keys())[:-1],  # Exclude "default" option
                format_func=lambda x: self.available_models[x],
                index=list(self.available_models.keys())[:-1].index(current_default) if current_default in self.available_models else 0,
                key="default_model_select"
            )
            
            if st.button("💾 Save Default Model", key="save_default_model"):
                self.settings["default_model"] = default_model
                if self._save_settings():
                    st.success("Default model updated!")
                    st.rerun()
        
        with col2:
            st.markdown("##### Expert Consultant Mode")
            current_expert = self.settings.get("expert_model", "gemini-1.5-pro")
            expert_model = st.selectbox(
                "Model for Expert Consultation",
                options=list(self.available_models.keys())[:-1],  # Exclude "default" option
                format_func=lambda x: self.available_models[x],
                index=list(self.available_models.keys())[:-1].index(current_expert) if current_expert in self.available_models else 1,
                key="expert_model_select"
            )
            
            if st.button("💾 Save Expert Model", key="save_expert_model"):
                self.settings["expert_model"] = expert_model
                if self._save_settings():
                    st.success("Expert model updated!")
                    st.rerun()
        
        st.markdown("---")
        
        # Model information
        st.markdown("#### 📊 Model Comparison")
        
        model_info = {
            "gemini-1.5-flash": {
                "Speed": "⚡⚡⚡⚡⚡ Very Fast",
                "Cost": "💰 Low",
                "Context Window": "1M tokens",
                "Best For": "Quick searches, simple queries",
                "Features": "Multimodal, efficient"
            },
            "gemini-1.5-pro": {
                "Speed": "⚡⚡⚡ Moderate",
                "Cost": "💰💰💰 Higher",
                "Context Window": "2M tokens",
                "Best For": "Complex analysis, expert consultation",
                "Features": "Most capable, best reasoning"
            },
            "gemini-1.0-pro": {
                "Speed": "⚡⚡⚡⚡ Fast",
                "Cost": "💰💰 Moderate",
                "Context Window": "32K tokens",
                "Best For": "Balanced performance",
                "Features": "Stable, reliable"
            }
        }
        
        for model, info in model_info.items():
            with st.expander(f"📋 {self.available_models[model]}", expanded=False):
                for key, value in info.items():
                    st.write(f"**{key}:** {value}")
        
        st.markdown("---")
        
        # User model preferences overview
        st.markdown("#### 👥 User Model Preferences")
        
        users_by_model = {}
        for username, user_data in self.users.items():
            model = user_data.get('model', 'default')
            if model not in users_by_model:
                users_by_model[model] = []
            users_by_model[model].append(username)
        
        for model, users in users_by_model.items():
            model_display = self.available_models.get(model, model)
            st.write(f"**{model_display}**: {', '.join(users)} ({len(users)} users)")
        
        # Current session info
        if hasattr(st.session_state, 'username'):
            current_user = self.users.get(st.session_state.username, {})
            user_model = current_user.get('model', 'default')
            st.info(f"💡 You are currently using: **{self.available_models.get(user_model, user_model)}**")
    
    def _render_cloud_storage(self):
        """Render cloud storage admin settings."""
        from cloud_storage import GoogleDriveManager
        from config import Config
        import os
        import json
        
        st.markdown("### ☁️ Cloud Storage Management")
        st.info("Configure cloud storage integration for all users. Only admins can manage cloud storage settings.")
        
        # Initialize fresh Google Drive manager
        gdrive = GoogleDriveManager()
        config = Config()
        
        # Check connection status
        if gdrive.load_saved_credentials():
            # CONNECTED STATE
            st.success("✅ Connected to Google Drive")
            
            # Disconnect button
            col1, col2 = st.columns([4, 1])
            with col2:
                if st.button("🔓 Disconnect", type="secondary", key="admin_disconnect_simple"):
                    # Complete cleanup
                    gdrive.credentials = None
                    gdrive.service = None
                    
                    # Clear session state
                    for key in ['gdrive_credentials', '_persistent_gdrive_creds']:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    # Clear environment
                    if 'GDRIVE_CREDENTIALS' in os.environ:
                        del os.environ['GDRIVE_CREDENTIALS']
                    
                    # Clear file
                    try:
                        if os.path.exists('.gdrive_credentials.json'):
                            os.remove('.gdrive_credentials.json')
                    except:
                        pass
                    
                    st.success("✅ Disconnected successfully!")
                    st.rerun()
            
            st.divider()
            
            # Show folder information
            if config.GOOGLE_DRIVE_FOLDER_ID:
                st.markdown(f"**📂 Main Folder:** Gemini Training")
                st.code(config.GOOGLE_DRIVE_FOLDER_ID)
                
                # Get and display subfolders with real counts
                with st.spinner("Loading folders..."):
                    subfolders = gdrive.list_folders(config.GOOGLE_DRIVE_FOLDER_ID)
                
                if subfolders:
                    st.markdown("**📁 Available Subfolders:**")
                    
                    # Show each subfolder with document count
                    for folder in subfolders:
                        with st.expander(f"📁 {folder['name']}", expanded=True):
                            # Get real document count with pagination
                            with st.spinner(f"Counting documents in {folder['name']}..."):
                                documents = gdrive.list_documents(folder['id'])
                            
                            st.info(f"📄 **{len(documents)} documents** found")
                            
                            # Sync button for this folder
                            if st.button(f"🚀 Sync {folder['name']} to Knowledge Base", 
                                       key=f"sync_{folder['id']}", type="primary"):
                                with st.spinner(f"Syncing {len(documents)} documents..."):
                                    # Clear documents folder first
                                    import shutil
                                    from pathlib import Path
                                    
                                    if Path(config.SOP_FOLDER).exists():
                                        shutil.rmtree(config.SOP_FOLDER)
                                    Path(config.SOP_FOLDER).mkdir(parents=True, exist_ok=True)
                                    
                                    # Download all files
                                    downloaded_files = gdrive.sync_folder(folder['id'], config.SOP_FOLDER)
                                    
                                    if downloaded_files:
                                        st.success(f"✅ Successfully synced {len(downloaded_files)} documents!")
                                        st.info("💡 Documents are now ready for the knowledge base.")
                                    else:
                                        st.error("❌ No documents were downloaded")
                            
                            # Show sample files
                            if documents:
                                with st.expander("📋 Show first 10 files", expanded=False):
                                    for i, doc in enumerate(documents[:10]):
                                        st.text(f"📄 {doc['name']}")
                                    if len(documents) > 10:
                                        st.text(f"... and {len(documents) - 10} more files")
                else:
                    st.warning("No subfolders found in main folder")
            
        else:
            # NOT CONNECTED STATE
            st.warning("🔗 Not connected to Google Drive")
            
            st.markdown("**To connect Google Drive:**")
            st.markdown("1. Get your OAuth credentials from Google Cloud Console")
            st.markdown("2. Paste the JSON configuration below")
            st.markdown("3. Complete the authentication flow")
            
            # Simple authentication flow
            client_config_text = st.text_area(
                "OAuth 2.0 Client Configuration (JSON):",
                placeholder='{"installed":{"client_id":"...","client_secret":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","redirect_uris":["urn:ietf:wg:oauth:2.0:oob","http://localhost"]}}',
                height=150
            )
            
            if client_config_text and st.button("🔐 Start Authentication", type="primary"):
                try:
                    client_config = json.loads(client_config_text)
                    auth_url, flow = gdrive.setup_oauth_flow(client_config)
                    
                    # Store flow in session state
                    st.session_state.oauth_flow = flow
                    st.session_state.client_config = client_config
                    
                    st.success("✅ Configuration valid!")
                    st.markdown(f"**[Click here to authorize access]({auth_url})**")
                    st.info("Copy the authorization code and paste it below:")
                    
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
                    if gdrive.authenticate_with_code(st.session_state.oauth_flow, auth_code):
                        st.success("🎉 Successfully connected to Google Drive!")
                        # Clean up session state
                        del st.session_state.oauth_flow
                        st.rerun()
                    else:
                        st.error("❌ Authentication failed")