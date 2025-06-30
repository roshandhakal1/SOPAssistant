"""
Authentication module for SOP Assistant
Provides secure login functionality with session management
"""

import streamlit as st
import hashlib
import hmac
from datetime import datetime, timedelta
import os
from typing import Dict, Optional
from user_manager import UserManager

class AuthManager:
    """Handles user authentication and session management."""
    
    def __init__(self):
        self.user_manager = UserManager()
        # Session timeout (4 hours)
        self.session_timeout = timedelta(hours=4)
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        return hmac.compare_digest(self._hash_password(password), password_hash)
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user with username and password."""
        return self.user_manager.authenticate(username, password)
    
    def is_session_valid(self) -> bool:
        """Check if current session is valid."""
        if "authenticated" not in st.session_state:
            return False
        
        if "login_time" not in st.session_state:
            return False
        
        # Check session timeout
        login_time = st.session_state.login_time
        if datetime.now() - login_time > self.session_timeout:
            self.logout()
            return False
        
        return st.session_state.authenticated
    
    def login(self, user_data: Dict) -> None:
        """Log in user and set session data."""
        st.session_state.authenticated = True
        st.session_state.username = user_data["username"]
        st.session_state.user_role = user_data["role"]
        st.session_state.user_name = user_data["name"]
        st.session_state.user_email = user_data.get("email", "")
        st.session_state.login_time = user_data["login_time"]
    
    def logout(self) -> None:
        """Log out user and clear session data."""
        for key in ["authenticated", "username", "user_role", "user_name", "user_email", "login_time"]:
            if key in st.session_state:
                del st.session_state[key]
    
    def render_login_page(self) -> bool:
        """Render login page and handle authentication."""
        st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <h1 style="color: #1d1d1f; font-size: 3rem; margin-bottom: 0.5rem;">🏭 SOP Assistant</h1>
            <p style="color: #86868b; font-size: 1.2rem; margin-bottom: 2rem;">Secure Manufacturing Intelligence Platform</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Center the login form
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            st.markdown("### 🔐 Sign In")
            
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                
                col_login, col_help = st.columns([1, 1])
                
                with col_login:
                    login_button = st.form_submit_button("Sign In", type="primary", use_container_width=True)
                
                with col_help:
                    if st.form_submit_button("Show Demo Credentials", use_container_width=True):
                        st.info("**Demo Credentials:**\n\n**Admin:** admin / admin123\n\n**User:** user / user123")
            
            if login_button:
                if username and password:
                    user_data = self.authenticate(username, password)
                    if user_data:
                        self.login(user_data)
                        st.success(f"Welcome back, {user_data['name']}!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
                else:
                    st.warning("⚠️ Please enter both username and password")
        
        # Footer
        st.markdown("""
        <div style="text-align: center; margin-top: 3rem; padding: 1rem; color: #86868b;">
            <p>🔒 Secure access to your manufacturing knowledge base</p>
        </div>
        """, unsafe_allow_html=True)
        
        return False
    
    def render_user_info(self) -> None:
        """Render user info in sidebar."""
        if self.is_session_valid():
            st.sidebar.markdown("---")
            st.sidebar.markdown("### 👤 User Session")
            st.sidebar.markdown(f"**Name:** {st.session_state.user_name}")
            st.sidebar.markdown(f"**Role:** {st.session_state.user_role.title()}")
            
            # Session time remaining
            time_elapsed = datetime.now() - st.session_state.login_time
            time_remaining = self.session_timeout - time_elapsed
            hours_remaining = int(time_remaining.total_seconds() // 3600)
            minutes_remaining = int((time_remaining.total_seconds() % 3600) // 60)
            
            if time_remaining.total_seconds() > 0:
                st.sidebar.caption(f"⏱️ Session: {hours_remaining}h {minutes_remaining}m remaining")
            
            if st.sidebar.button("🚪 Sign Out", type="secondary", use_container_width=True):
                self.logout()
                st.rerun()

def require_auth():
    """Decorator function to require authentication for app access."""
    auth_manager = AuthManager()
    
    if not auth_manager.is_session_valid():
        auth_manager.render_login_page()
        st.stop()
    else:
        # Add user info to sidebar
        auth_manager.render_user_info()
        return auth_manager