"""
Enhanced security module for SOP Assistant
Implements corporate-grade security measures
"""

import streamlit as st
import hashlib
import hmac
import secrets
import bcrypt
import re
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import logging
from functools import wraps
import time

# Configure security logging
logging.basicConfig(
    filename='security_audit.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
security_logger = logging.getLogger('security')

class RateLimiter:
    """Rate limiting for authentication attempts"""
    
    def __init__(self, max_attempts: int = 5, window_minutes: int = 15):
        self.max_attempts = max_attempts
        self.window = timedelta(minutes=window_minutes)
        self.attempts = {}
        self.lockout_file = ".lockout_cache.json"
        self._load_lockouts()
    
    def _load_lockouts(self):
        """Load lockout data from file"""
        try:
            if os.path.exists(self.lockout_file):
                with open(self.lockout_file, 'r') as f:
                    data = json.load(f)
                    # Convert string timestamps back to datetime
                    for key, value in data.items():
                        self.attempts[key] = [
                            datetime.fromisoformat(ts) for ts in value
                        ]
        except Exception:
            self.attempts = {}
    
    def _save_lockouts(self):
        """Save lockout data to file"""
        try:
            data = {}
            for key, timestamps in self.attempts.items():
                # Keep only recent attempts
                recent = [ts for ts in timestamps if datetime.now() - ts < self.window]
                if recent:
                    data[key] = [ts.isoformat() for ts in recent]
            
            with open(self.lockout_file, 'w') as f:
                json.dump(data, f)
            os.chmod(self.lockout_file, 0o600)  # Secure file permissions
        except Exception:
            pass
    
    def check_rate_limit(self, identifier: str) -> Tuple[bool, int]:
        """Check if identifier is rate limited"""
        now = datetime.now()
        
        # Clean old attempts
        if identifier in self.attempts:
            self.attempts[identifier] = [
                ts for ts in self.attempts[identifier] 
                if now - ts < self.window
            ]
        
        # Check current attempts
        attempt_count = len(self.attempts.get(identifier, []))
        
        if attempt_count >= self.max_attempts:
            security_logger.warning(f"Rate limit exceeded for {identifier}")
            return False, self.max_attempts - attempt_count
        
        return True, self.max_attempts - attempt_count
    
    def record_attempt(self, identifier: str):
        """Record an authentication attempt"""
        if identifier not in self.attempts:
            self.attempts[identifier] = []
        
        self.attempts[identifier].append(datetime.now())
        self._save_lockouts()
    
    def clear_attempts(self, identifier: str):
        """Clear attempts for successful login"""
        if identifier in self.attempts:
            del self.attempts[identifier]
            self._save_lockouts()

class InputValidator:
    """Validate and sanitize user inputs"""
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """Validate username format"""
        if not username:
            return False, "Username cannot be empty"
        
        if len(username) < 3 or len(username) > 20:
            return False, "Username must be 3-20 characters"
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return False, "Username can only contain letters, numbers, hyphens, and underscores"
        
        # Prevent dangerous usernames
        forbidden = ['admin', 'root', 'system', 'null', 'undefined']
        if username.lower() in forbidden:
            return False, "This username is not allowed"
        
        return True, ""
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """Validate password complexity"""
        if len(password) < 12:
            return False, "Password must be at least 12 characters"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain uppercase letters"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain lowercase letters"
        
        if not re.search(r'[0-9]', password):
            return False, "Password must contain numbers"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain special characters"
        
        # Check against common passwords
        common_passwords = ['password123', 'admin123', 'Password123!', 'Welcome123!']
        if password in common_passwords:
            return False, "This password is too common"
        
        return True, ""
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Invalid email format"
        return True, ""
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 255) -> str:
        """Sanitize user input to prevent injection attacks"""
        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32)
        
        # Truncate to max length
        text = text[:max_length]
        
        # Escape HTML special characters
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&#x27;')
        
        return text.strip()

class SecureAuthManager:
    """Enhanced authentication manager with corporate security features"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.validator = InputValidator()
        self.session_timeout = timedelta(hours=2)
        self.secure_users_file = ".secure_users.json"
        self.session_tokens = {}
        
        # Initialize secure storage
        self._init_secure_storage()
    
    def _init_secure_storage(self):
        """Initialize secure user storage"""
        if not os.path.exists(self.secure_users_file):
            # Create with secure default admin
            default_data = {
                "users": {
                    "admin": {
                        "username": "admin",
                        "password_hash": bcrypt.hashpw(b"ChangeMe123!@#", bcrypt.gensalt()).decode('utf-8'),
                        "role": "admin",
                        "name": "Administrator",
                        "email": "admin@company.com",
                        "created_at": datetime.now().isoformat(),
                        "last_login": None,
                        "failed_attempts": 0,
                        "locked_until": None,
                        "must_change_password": True,
                        "password_history": []
                    }
                },
                "config": {
                    "password_expiry_days": 90,
                    "max_login_attempts": 5,
                    "lockout_duration_minutes": 30,
                    "session_timeout_hours": 2,
                    "require_2fa": False
                }
            }
            
            with open(self.secure_users_file, 'w') as f:
                json.dump(default_data, f, indent=2)
            
            # Set secure file permissions (owner read/write only)
            os.chmod(self.secure_users_file, 0o600)
            
            security_logger.info("Initialized secure user storage")
    
    def _load_users(self) -> Dict:
        """Load users from secure storage"""
        try:
            with open(self.secure_users_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            security_logger.error(f"Failed to load users: {e}")
            return {"users": {}, "config": {}}
    
    def _save_users(self, data: Dict):
        """Save users to secure storage"""
        try:
            # Write to temporary file first
            temp_file = f"{self.secure_users_file}.tmp"
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Set secure permissions
            os.chmod(temp_file, 0o600)
            
            # Atomic rename
            os.rename(temp_file, self.secure_users_file)
            
        except Exception as e:
            security_logger.error(f"Failed to save users: {e}")
            raise
    
    def authenticate(self, username: str, password: str, ip_address: str = "unknown") -> Optional[Dict]:
        """Authenticate user with enhanced security"""
        # Validate inputs
        username = self.validator.sanitize_input(username, 20)
        
        # Check rate limit
        identifier = f"{username}:{ip_address}"
        allowed, remaining = self.rate_limiter.check_rate_limit(identifier)
        
        if not allowed:
            security_logger.warning(f"Rate limit exceeded for {username} from {ip_address}")
            return None
        
        # Record attempt
        self.rate_limiter.record_attempt(identifier)
        
        # Load users
        data = self._load_users()
        users = data.get("users", {})
        
        # Check if user exists
        if username not in users:
            security_logger.warning(f"Login attempt for non-existent user: {username}")
            time.sleep(2)  # Prevent timing attacks
            return None
        
        user = users[username]
        
        # Check if account is locked
        if user.get("locked_until"):
            locked_until = datetime.fromisoformat(user["locked_until"])
            if datetime.now() < locked_until:
                security_logger.warning(f"Login attempt for locked account: {username}")
                return None
            else:
                # Unlock account
                user["locked_until"] = None
                user["failed_attempts"] = 0
        
        # Verify password
        try:
            password_valid = bcrypt.checkpw(
                password.encode('utf-8'), 
                user["password_hash"].encode('utf-8')
            )
        except Exception:
            password_valid = False
        
        if not password_valid:
            # Record failed attempt
            user["failed_attempts"] = user.get("failed_attempts", 0) + 1
            
            # Lock account if too many failures
            if user["failed_attempts"] >= data["config"]["max_login_attempts"]:
                lockout_minutes = data["config"]["lockout_duration_minutes"]
                user["locked_until"] = (datetime.now() + timedelta(minutes=lockout_minutes)).isoformat()
                security_logger.warning(f"Account locked due to failed attempts: {username}")
            
            self._save_users(data)
            security_logger.warning(f"Failed login attempt for user: {username}")
            return None
        
        # Successful authentication
        user["failed_attempts"] = 0
        user["last_login"] = datetime.now().isoformat()
        self._save_users(data)
        
        # Clear rate limit
        self.rate_limiter.clear_attempts(identifier)
        
        # Generate session token
        session_token = secrets.token_urlsafe(32)
        self.session_tokens[session_token] = {
            "username": username,
            "created": datetime.now(),
            "ip_address": ip_address
        }
        
        security_logger.info(f"Successful login for user: {username} from {ip_address}")
        
        return {
            "username": username,
            "role": user["role"],
            "name": user["name"],
            "email": user["email"],
            "session_token": session_token,
            "must_change_password": user.get("must_change_password", False),
            "login_time": datetime.now()
        }
    
    def verify_session_token(self, token: str) -> Optional[str]:
        """Verify session token and return username"""
        if token not in self.session_tokens:
            return None
        
        session = self.session_tokens[token]
        
        # Check timeout
        if datetime.now() - session["created"] > self.session_timeout:
            del self.session_tokens[token]
            return None
        
        return session["username"]
    
    def create_user(self, username: str, password: str, role: str, name: str, 
                   email: str, created_by: str) -> Tuple[bool, str]:
        """Create new user with validation"""
        # Validate inputs
        valid, msg = self.validator.validate_username(username)
        if not valid:
            return False, msg
        
        valid, msg = self.validator.validate_password(password)
        if not valid:
            return False, msg
        
        valid, msg = self.validator.validate_email(email)
        if not valid:
            return False, msg
        
        # Sanitize inputs
        username = self.validator.sanitize_input(username, 20)
        name = self.validator.sanitize_input(name, 50)
        email = self.validator.sanitize_input(email, 100)
        
        # Load users
        data = self._load_users()
        users = data.get("users", {})
        
        # Check if user exists
        if username in users:
            return False, "Username already exists"
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create user
        users[username] = {
            "username": username,
            "password_hash": password_hash,
            "role": role,
            "name": name,
            "email": email,
            "created_at": datetime.now().isoformat(),
            "created_by": created_by,
            "last_login": None,
            "failed_attempts": 0,
            "locked_until": None,
            "must_change_password": False,
            "password_history": [password_hash]
        }
        
        data["users"] = users
        self._save_users(data)
        
        security_logger.info(f"User created: {username} by {created_by}")
        return True, "User created successfully"
    
    def change_password(self, username: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Change user password with validation"""
        # Validate new password
        valid, msg = self.validator.validate_password(new_password)
        if not valid:
            return False, msg
        
        # Load users
        data = self._load_users()
        users = data.get("users", {})
        
        if username not in users:
            return False, "User not found"
        
        user = users[username]
        
        # Verify old password
        if not bcrypt.checkpw(old_password.encode('utf-8'), user["password_hash"].encode('utf-8')):
            security_logger.warning(f"Failed password change attempt for user: {username}")
            return False, "Current password is incorrect"
        
        # Check password history
        for old_hash in user.get("password_history", [])[-5:]:  # Check last 5 passwords
            if bcrypt.checkpw(new_password.encode('utf-8'), old_hash.encode('utf-8')):
                return False, "Cannot reuse recent passwords"
        
        # Hash new password
        new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Update user
        user["password_hash"] = new_hash
        user["must_change_password"] = False
        user["password_changed_at"] = datetime.now().isoformat()
        
        # Update password history
        if "password_history" not in user:
            user["password_history"] = []
        user["password_history"].append(new_hash)
        user["password_history"] = user["password_history"][-10:]  # Keep last 10
        
        self._save_users(data)
        
        security_logger.info(f"Password changed for user: {username}")
        return True, "Password changed successfully"
    
    def logout(self, session_token: str):
        """Logout user and invalidate session"""
        if session_token in self.session_tokens:
            username = self.session_tokens[session_token]["username"]
            del self.session_tokens[session_token]
            security_logger.info(f"User logged out: {username}")

# Audit decorator for sensitive operations
def audit_action(action: str):
    """Decorator to audit sensitive actions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            username = st.session_state.get('username', 'unknown')
            security_logger.info(f"AUDIT: {action} by {username}")
            try:
                result = func(*args, **kwargs)
                security_logger.info(f"AUDIT: {action} completed successfully by {username}")
                return result
            except Exception as e:
                security_logger.error(f"AUDIT: {action} failed for {username}: {str(e)}")
                raise
        return wrapper
    return decorator