"""
User Settings Interface for SOP Assistant
Allows users to manage their own settings, passwords, and preferences
"""

import streamlit as st
import bcrypt
from datetime import datetime
from typing import Dict, Optional
from user_manager import UserManager
from secure_auth import SecureAuthManager, InputValidator

class UserSettingsInterface:
    """Interface for users to manage their own settings"""
    
    def __init__(self):
        self.user_manager = UserManager()
        self.secure_auth = SecureAuthManager()
        self.validator = InputValidator()
    
    def render_user_settings_page(self):
        """Render the user settings page"""
        if not st.session_state.get('authenticated', False):
            st.error("Please log in to access settings")
            return
        
        username = st.session_state.get('username', '')
        user_data = self.user_manager.users.get(username, {})
        
        if not user_data:
            st.error("User data not found")
            return
        
        st.markdown("# ⚙️ My Settings")
        st.markdown(f"**Welcome, {user_data.get('name', username)}!**")
        
        # Create tabs for different settings
        tab1, tab2, tab3 = st.tabs(["🔐 Password", "🤖 AI Models", "👤 Profile"])
        
        with tab1:
            self._render_password_change(username, user_data)
        
        with tab2:
            self._render_model_preferences(username, user_data)
        
        with tab3:
            self._render_profile_settings(username, user_data)
    
    def _render_password_change(self, username: str, user_data: Dict):
        """Render password change interface"""
        st.markdown("### 🔐 Change Password")
        
        # Check if user must change password
        if user_data.get('must_change_password', False):
            st.warning("⚠️ You must change your password before continuing to use the application.")
        
        with st.form("change_my_password"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password", help="Minimum 12 characters with uppercase, lowercase, numbers, and special characters")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            # Show password requirements
            with st.expander("🔍 Password Requirements", expanded=False):
                st.markdown("""
                **Your password must have:**
                - At least 12 characters
                - At least one uppercase letter (A-Z)
                - At least one lowercase letter (a-z)
                - At least one number (0-9)
                - At least one special character (!@#$%^&*...)
                - Cannot be a common password
                """)
            
            if st.form_submit_button("🔄 Change Password", type="primary"):
                if not current_password:
                    st.error("❌ Please enter your current password")
                elif not new_password or not confirm_password:
                    st.error("❌ Please fill in all password fields")
                elif new_password != confirm_password:
                    st.error("❌ New passwords do not match")
                else:
                    # Validate current password
                    auth_result = self.user_manager.authenticate(username, current_password)
                    if not auth_result:
                        st.error("❌ Current password is incorrect")
                    else:
                        # Validate new password
                        valid, error_msg = self.validator.validate_password(new_password)
                        if not valid:
                            st.error(f"❌ {error_msg}")
                        else:
                            # Change password
                            success, message = self.secure_auth.change_password(
                                username, current_password, new_password
                            )
                            
                            if success:
                                # Update legacy system
                                hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                                
                                self.user_manager.users[username]['password'] = new_password  # Legacy
                                self.user_manager.users[username]['password_hash'] = hashed_password
                                self.user_manager.users[username]['must_change_password'] = False
                                self.user_manager.users[username]['password_changed_at'] = datetime.now().isoformat()
                                self.user_manager.users[username]['password_changed_by'] = username
                                
                                self.user_manager._save_users()
                                
                                st.success("✅ Password changed successfully!")
                                st.info("ℹ️ You will need to log in again with your new password.")
                                
                                # Log out user to force re-login
                                if st.button("🚪 Log Out Now"):
                                    from auth import AuthManager
                                    auth_manager = AuthManager()
                                    auth_manager.logout()
                                    st.rerun()
                            else:
                                st.error(f"❌ {message}")
    
    def _render_model_preferences(self, username: str, user_data: Dict):
        """Render model preference settings"""
        st.markdown("### 🤖 AI Model Preferences")
        
        st.info("Choose which AI models to use for different types of queries. Using more powerful models may be slower but provide better responses.")
        
        with st.form("my_model_preferences"):
            current_standard = user_data.get('standard_model', 'default')
            current_expert = user_data.get('expert_model', 'default')
            
            # Model options
            model_options = ["default"] + list(self.user_manager.available_models.keys())
            model_labels = ["🌐 Use Global Default"] + [f"🤖 {self.user_manager.available_models[k]}" for k in self.user_manager.available_models.keys()]
            
            # Current selections
            standard_index = model_options.index(current_standard) if current_standard in model_options else 0
            expert_index = model_options.index(current_expert) if current_expert in model_options else 0
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📚 Standard Search Model")
                st.caption("Used for general knowledge searches and document queries")
                
                new_standard = st.selectbox(
                    "Choose model:",
                    options=model_options,
                    format_func=lambda x: model_labels[model_options.index(x)],
                    index=standard_index,
                    key="standard_model_select"
                )
                
                # Show model info
                if new_standard != "default":
                    self._show_model_info(new_standard)
            
            with col2:
                st.markdown("#### 🎯 Expert Consultation Model")
                st.caption("Used when consulting with specialized experts (@QualityExpert, etc.)")
                
                new_expert = st.selectbox(
                    "Choose model:",
                    options=model_options,
                    format_func=lambda x: model_labels[model_options.index(x)],
                    index=expert_index,
                    key="expert_model_select"
                )
                
                # Show model info
                if new_expert != "default":
                    self._show_model_info(new_expert)
            
            if st.form_submit_button("💾 Save Model Preferences", type="primary"):
                self.user_manager.users[username]['standard_model'] = new_standard
                self.user_manager.users[username]['expert_model'] = new_expert
                self.user_manager.users[username]['model_preferences_updated_at'] = datetime.now().isoformat()
                
                self.user_manager._save_users()
                st.success("✅ Model preferences saved!")
                st.rerun()
    
    def _show_model_info(self, model_key: str):
        """Show information about a specific model"""
        model_info = {
            "gemini-1.5-flash": {
                "description": "Fast and efficient for quick responses",
                "speed": "⚡⚡⚡⚡⚡",
                "quality": "⭐⭐⭐⭐",
                "best_for": "General queries, fast responses"
            },
            "gemini-1.5-pro": {
                "description": "Advanced model for complex analysis",
                "speed": "⚡⚡⚡",
                "quality": "⭐⭐⭐⭐⭐",
                "best_for": "Expert consultations, detailed analysis"
            },
            "gemini-1.0-pro": {
                "description": "Stable and reliable for production use",
                "speed": "⚡⚡⚡⚡",
                "quality": "⭐⭐⭐⭐",
                "best_for": "Consistent responses, stability"
            }
        }
        
        if model_key in model_info:
            info = model_info[model_key]
            st.caption(f"**{info['description']}**")
            st.caption(f"Speed: {info['speed']} | Quality: {info['quality']}")
            st.caption(f"Best for: {info['best_for']}")
    
    def _render_profile_settings(self, username: str, user_data: Dict):
        """Render profile settings"""
        st.markdown("### 👤 Profile Information")
        
        with st.form("my_profile"):
            st.text_input("Username", value=username, disabled=True, help="Username cannot be changed")
            
            current_name = user_data.get('name', '')
            current_email = user_data.get('email', '')
            
            new_name = st.text_input("Full Name", value=current_name, max_chars=50)
            new_email = st.text_input("Email Address", value=current_email, max_chars=100)
            
            # Show account info
            st.markdown("#### 📊 Account Information")
            col1, col2 = st.columns(2)
            
            with col1:
                st.text(f"Role: {user_data.get('role', 'user').title()}")
                st.text(f"Status: {'🟢 Active' if user_data.get('active', True) else '🔴 Inactive'}")
            
            with col2:
                created_at = user_data.get('created_at', 'Unknown')
                if created_at != 'Unknown':
                    try:
                        created_date = datetime.fromisoformat(created_at).strftime('%Y-%m-%d')
                        st.text(f"Member since: {created_date}")
                    except:
                        st.text("Member since: Unknown")
                
                last_login = user_data.get('last_login', 'Never')
                if last_login and last_login != 'Never':
                    try:
                        login_date = datetime.fromisoformat(last_login).strftime('%Y-%m-%d %H:%M')
                        st.text(f"Last login: {login_date}")
                    except:
                        st.text("Last login: Unknown")
            
            if st.form_submit_button("💾 Update Profile", type="primary"):
                # Validate inputs
                if not new_name.strip():
                    st.error("❌ Name cannot be empty")
                elif new_email and not self._validate_email(new_email):
                    st.error("❌ Invalid email format")
                else:
                    # Update profile
                    self.user_manager.users[username]['name'] = new_name.strip()
                    if new_email:
                        self.user_manager.users[username]['email'] = new_email.strip()
                    
                    self.user_manager.users[username]['profile_updated_at'] = datetime.now().isoformat()
                    self.user_manager.users[username]['profile_updated_by'] = username
                    
                    self.user_manager._save_users()
                    
                    # Update session state
                    st.session_state.user_name = new_name.strip()
                    if new_email:
                        st.session_state.user_email = new_email.strip()
                    
                    st.success("✅ Profile updated successfully!")
                    st.rerun()
    
    def _validate_email(self, email: str) -> bool:
        """Simple email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None