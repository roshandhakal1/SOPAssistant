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
    
    def __init__(self, users_file: str = "users.json"):
        self.users_file = users_file
        self.users = self._load_users()
    
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
    
    def add_user(self, username: str, password: str, name: str, email: str, role: str = "user") -> bool:
        """Add a new user."""
        if username in self.users:
            return False
        
        self.users[username] = {
            "password": password,
            "role": role,
            "name": name,
            "email": email,
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
            if key in ["password", "role", "name", "email", "active"]:
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
    
    def render_admin_portal(self):
        """Render the admin user management portal."""
        if not hasattr(st.session_state, 'user_role') or st.session_state.user_role != 'admin':
            st.error("🚫 Access denied. Admin privileges required.")
            return
        
        st.markdown("## 👥 User Management Portal")
        
        # Tabs for different admin functions
        tab1, tab2, tab3 = st.tabs(["📋 All Users", "➕ Add User", "⚙️ User Settings"])
        
        with tab1:
            self._render_users_list()
        
        with tab2:
            self._render_add_user()
        
        with tab3:
            self._render_user_settings()
    
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
                        new_password = st.text_input("New Password (leave blank to keep current)", 
                                                   type="password")
                        
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.form_submit_button("💾 Save Changes", type="primary"):
                                updates = {"name": new_name, "email": new_email, "role": new_role}
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
                    if self.add_user(username, password, name, email, role):
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