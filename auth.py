"""
Authentication module for SOP Assistant
Provides secure login functionality with session management
"""

import streamlit as st
import hashlib
import hmac
from datetime import datetime, timedelta
import os
import json
from typing import Dict, Optional
from user_manager import UserManager
from secure_auth import SecureAuthManager, audit_action
import secrets

class AuthManager:
    """Handles user authentication and session management."""
    
    def __init__(self):
        self.user_manager = UserManager()
        self.secure_auth = SecureAuthManager()
        # SECURITY FIX: Shorter, more secure session timeouts
        self.session_timeout = timedelta(hours=2)  # 2 hours for normal session
        self.remember_timeout = timedelta(days=7)  # 7 days max for remember me
        
        # Generate CSRF token for session
        if 'csrf_token' not in st.session_state:
            st.session_state.csrf_token = secrets.token_urlsafe(32)
        
        # Initialize session persistence
        self._init_session_persistence()
    
    def _init_session_persistence(self) -> None:
        """Initialize session persistence on startup."""
        # Try to load persistent session if not already authenticated
        if "authenticated" not in st.session_state:
            self._load_persistent_session()
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        return hmac.compare_digest(self._hash_password(password), password_hash)
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user with username and password."""
        # Use legacy authentication directly for now (bypassing secure system temporarily)
        result = self.user_manager.authenticate(username, password)
        return result
    
    def is_session_valid(self) -> bool:
        """Check if current session is valid."""
        if "authenticated" not in st.session_state:
            return False
        
        if "login_time" not in st.session_state:
            return False
        
        # Verify session token if using secure auth
        if 'session_token' in st.session_state:
            username = self.secure_auth.verify_session_token(st.session_state.session_token)
            if not username or username != st.session_state.username:
                self.logout()
                return False
        
        # Check session timeout
        login_time = st.session_state.login_time
        timeout = self.session_timeout
        
        if datetime.now() - login_time > timeout:
            self.logout()
            return False
        
        # Verify CSRF token
        if 'csrf_token' not in st.session_state:
            self.logout()
            return False
        
        return st.session_state.authenticated
    
    @audit_action("user_login")
    def login(self, user_data: Dict, remember_me: bool = False) -> None:
        """Log in user and set session data."""
        # First, clear any existing session data to prevent cross-user contamination
        self._clear_session_data()
        
        # Set new user session data
        st.session_state.authenticated = True
        st.session_state.username = user_data["username"]
        st.session_state.user_role = user_data["role"]
        st.session_state.user_name = user_data["name"]
        st.session_state.user_email = user_data.get("email", "")
        st.session_state.login_time = user_data["login_time"]
        st.session_state.remember_me = False  # Disabled for security
        
        # Store session token if available
        if 'session_token' in user_data:
            st.session_state.session_token = user_data['session_token']
        
        # Store password change flag
        if 'must_change_password' in user_data:
            st.session_state.must_change_password = user_data['must_change_password']
        
        # Initialize clean session state for this user
        st.session_state.messages = []
        st.session_state.mode = "standard"
        st.session_state.uploaded_documents = []
        
        # Note: Persistent sessions disabled for security
    
    @audit_action("user_logout")
    def logout(self) -> None:
        """Log out user and clear session data."""
        # Invalidate session token
        if 'session_token' in st.session_state:
            self.secure_auth.logout(st.session_state.session_token)
        
        # Clear persistent storage
        self._clear_persistent_session()
        
        # Clear ALL session state to prevent data leakage between users
        keys_to_clear = [
            "authenticated", "username", "user_role", "user_name", "user_email", 
            "login_time", "remember_me", "messages", "mode", "uploaded_documents",
            "components", "initialized", "show_admin_portal", "attached_documents",
            "selected_mode", "selected_experts", "current_expert_input",
            "expert_input_key", "session_token", "csrf_token", "must_change_password"
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    def _clear_session_data(self) -> None:
        """Clear session data that could leak between users."""
        keys_to_clear = [
            "messages", "mode", "uploaded_documents", "components", 
            "initialized", "show_admin_portal", "attached_documents",
            "selected_mode", "selected_experts", "current_expert_input",
            "expert_input_key", "messages", "mode"
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    def render_login_page(self) -> bool:
        """Render login page and handle authentication."""
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@300;400;500;600;700;800&display=swap');
        
        .login-title {
            font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 4rem;
            font-weight: 800;
            margin: 0 0 0.5rem 0;
            letter-spacing: -0.05em;
            color: #1d1d1f;
            line-height: 0.9;
            animation: fadeInTitle 1s ease-out forwards;
        }
        
        .login-subtitle {
            font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 1.3rem;
            font-weight: 500;
            margin: 0.5rem 0 2rem 0;
            background: linear-gradient(135deg, #6e6e73 0%, #86868b 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -0.02em;
            animation: fadeInSubtitle 1s ease-out forwards 0.3s;
            opacity: 0;
        }
        
        @keyframes fadeInTitle {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes fadeInSubtitle {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        </style>
        
        <div style="text-align: center; padding: 2rem 0;">
            <h1 class="login-title">SOP Assistant</h1>
            <p class="login-subtitle">Manufacturing Intelligence Platform</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Center the login form
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            st.markdown("### Sign In")
            
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                remember_me = st.checkbox("Remember me for 7 days", value=False)
                
                login_button = st.form_submit_button("Sign In", type="primary", use_container_width=True)
            
            if login_button:
                if username and password:
                    user_data = self.authenticate(username, password)
                    if user_data:
                        self.login(user_data, remember_me)
                        st.success(f"Welcome back, {user_data['name']}!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
                else:
                    st.warning("⚠️ Please enter both username and password")
        
        # Footer
        st.markdown("""
        <div style="text-align: center; margin-top: 3rem; padding: 1rem; color: #86868b;">
            <p>Secure access to your manufacturing knowledge base</p>
        </div>
        """, unsafe_allow_html=True)
        
        return False
    
    def _save_persistent_session(self, user_data: Dict) -> None:
        """Save session data for persistent login."""
        # SECURITY: Disabled persistent sessions to prevent unauthorized access
        # The persistent session feature was allowing users to access other users' accounts
        # by loading session files from the server. This is a critical security vulnerability.
        # For proper persistent sessions, use secure browser cookies or a database with proper authentication.
        pass
    
    def _load_persistent_session(self) -> bool:
        """Load session data from persistent storage."""
        # SECURITY: Disabled persistent sessions to prevent unauthorized access
        # The persistent session feature was allowing users to access other users' accounts
        # by loading session files from the server. This is a critical security vulnerability.
        # For proper persistent sessions, use secure browser cookies or a database with proper authentication.
        return False
    
    def _clear_persistent_session(self) -> None:
        """Clear persistent session storage."""
        # SECURITY: Disabled persistent sessions to prevent unauthorized access
        # Clean up any existing session files if they exist
        try:
            import glob
            
            # Remove all session files to ensure no lingering security vulnerabilities
            session_files = glob.glob(".session_*.json")
            for session_file in session_files:
                try:
                    os.remove(session_file)
                except:
                    pass
            
        except Exception:
            pass
    
    def render_user_info(self) -> None:
        """Render user info in main header area."""
        if self.is_session_valid():
            # Get time-based greeting
            from datetime import datetime
            import pytz
            
            # Get PST time
            pst = pytz.timezone('US/Pacific')
            current_time = datetime.now(pst)
            hour = current_time.hour
            
            if 5 <= hour < 12:
                greeting = "Good morning"
            elif 12 <= hour < 17:
                greeting = "Good afternoon"
            else:
                greeting = "Good evening"
            
            # Add user info and sign out to the top right of main area
            col1, col2, col3 = st.columns([4, 1.5, 0.5])
            
            with col2:
                st.markdown(f"""
                <div style="text-align: right; padding: 0.5rem 0; color: #6e6e73; font-size: 0.875rem;">
                    {greeting}, {st.session_state.user_name} <span style="color: #86868b;">({st.session_state.user_role})</span>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                if st.button("Sign Out", type="secondary", help="Sign out of your account", key="header_signout", use_container_width=True):
                    self.logout()
                    st.rerun()

    def _migrate_user_to_secure(self, username: str, password: str, user_data: Dict):
        """Migrate user from legacy system to secure system"""
        try:
            # Create user in secure system
            self.secure_auth.create_user(
                username=username,
                password=password,
                role=user_data.get("role", "user"),
                name=user_data.get("name", username),
                email=user_data.get("email", f"{username}@company.com"),
                created_by="migration"
            )
        except Exception:
            pass  # Ignore if already exists

def require_auth():
    """Decorator function to require authentication for app access."""
    auth_manager = AuthManager()
    
    if not auth_manager.is_session_valid():
        auth_manager.render_login_page()
        st.stop()
    else:
        # Don't render user info here - it will be called from main()
        return auth_manager