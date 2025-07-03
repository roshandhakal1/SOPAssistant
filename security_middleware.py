"""
Security middleware for SOP Assistant
Provides additional security layers for the application
"""

import streamlit as st
import re
import html
from typing import Any, Dict, List
import hashlib
import json
from datetime import datetime
import logging

# Configure security logging
security_logger = logging.getLogger('security.middleware')

class SecurityMiddleware:
    """Security middleware for the application"""
    
    @staticmethod
    def set_security_headers():
        """Set security headers for the application"""
        # Note: Streamlit doesn't support direct header manipulation
        # These would be set at the reverse proxy/web server level
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline';",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }
        return headers
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Sanitize HTML content to prevent XSS"""
        # Escape HTML entities
        text = html.escape(text)
        
        # Additional sanitization for common XSS patterns
        xss_patterns = [
            r'<script.*?>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe.*?>.*?</iframe>',
            r'<object.*?>.*?</object>',
            r'<embed.*?>',
            r'<link.*?>'
        ]
        
        for pattern in xss_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text
    
    @staticmethod
    def validate_file_upload(file) -> tuple[bool, str]:
        """Validate uploaded files for security"""
        # Check file size (max 50MB)
        MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
        
        if file.size > MAX_FILE_SIZE:
            return False, "File size exceeds 50MB limit"
        
        # Check file extension
        ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt', '.csv', '.md'}
        file_ext = '.' + file.name.split('.')[-1].lower()
        
        if file_ext not in ALLOWED_EXTENSIONS:
            return False, f"File type {file_ext} not allowed"
        
        # Check for double extensions
        if file.name.count('.') > 1:
            # Check for dangerous double extensions
            dangerous_patterns = ['.exe.', '.bat.', '.cmd.', '.com.', '.scr.', '.vbs.', '.js.']
            for pattern in dangerous_patterns:
                if pattern in file.name.lower():
                    return False, "Suspicious file name detected"
        
        # Check MIME type
        mime_type_mapping = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.txt': 'text/plain',
            '.csv': 'text/csv',
            '.md': 'text/markdown'
        }
        
        # Validate file content matches extension
        # Read first few bytes to check file signature
        file_content = file.read(8)
        file.seek(0)  # Reset file pointer
        
        # Check file signatures
        if file_ext == '.pdf' and not file_content.startswith(b'%PDF'):
            return False, "Invalid PDF file"
        
        if file_ext == '.docx':
            # DOCX files start with PK (ZIP format)
            if not file_content.startswith(b'PK'):
                return False, "Invalid DOCX file"
        
        return True, "File validation passed"
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent directory traversal"""
        # Remove path separators
        filename = filename.replace('/', '').replace('\\', '')
        
        # Remove special characters
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
        
        # Limit length
        max_length = 255
        if len(filename) > max_length:
            name, ext = filename.rsplit('.', 1)
            filename = name[:max_length-len(ext)-1] + '.' + ext
        
        return filename
    
    @staticmethod
    def validate_search_query(query: str) -> tuple[bool, str]:
        """Validate search queries to prevent injection"""
        # Check length
        if len(query) > 1000:
            return False, "Query too long (max 1000 characters)"
        
        # Check for injection patterns
        injection_patterns = [
            r'\$where',
            r'[\{\}]',
            r'function\s*\(',
            r'return\s+',
            r'<script',
            r'javascript:',
            r'\beval\b',
            r'\bexec\b'
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return False, "Invalid characters in query"
        
        return True, "Query validation passed"
    
    @staticmethod
    def hash_sensitive_data(data: str) -> str:
        """Hash sensitive data for logging"""
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    @staticmethod
    def redact_sensitive_info(text: str) -> str:
        """Redact sensitive information from logs"""
        # Redact email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
        
        # Redact credit card numbers
        text = re.sub(r'\b(?:\d{4}[\s-]?){3}\d{4}\b', '[CARD]', text)
        
        # Redact SSN
        text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)
        
        # Redact phone numbers
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
        
        # Redact API keys (common patterns)
        text = re.sub(r'\b[A-Za-z0-9]{32,}\b', '[API_KEY]', text)
        
        return text
    
    @staticmethod
    def check_session_hijacking(session_data: Dict) -> bool:
        """Check for potential session hijacking"""
        # Check if IP address changed (if tracking)
        current_ip = st.session_state.get('client_ip', 'unknown')
        session_ip = session_data.get('ip_address', 'unknown')
        
        if current_ip != 'unknown' and session_ip != 'unknown' and current_ip != session_ip:
            security_logger.warning(f"Potential session hijacking detected: IP changed from {session_ip} to {current_ip}")
            return True
        
        # Check if user agent changed (if tracking)
        current_ua = st.session_state.get('user_agent', 'unknown')
        session_ua = session_data.get('user_agent', 'unknown')
        
        if current_ua != 'unknown' and session_ua != 'unknown' and current_ua != session_ua:
            security_logger.warning("Potential session hijacking detected: User agent changed")
            return True
        
        return False
    
    @staticmethod
    def log_security_event(event_type: str, details: Dict):
        """Log security events for monitoring"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "username": st.session_state.get('username', 'anonymous'),
            "ip_address": st.session_state.get('client_ip', 'unknown'),
            "details": SecurityMiddleware.redact_sensitive_info(json.dumps(details))
        }
        
        security_logger.info(f"SECURITY_EVENT: {json.dumps(event)}")
    
    @staticmethod
    def enforce_content_security_policy(content: str) -> str:
        """Enforce content security policy on user-generated content"""
        # Remove inline scripts
        content = re.sub(r'<script.*?>.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove inline event handlers
        content = re.sub(r'\bon\w+\s*=\s*["\'].*?["\']', '', content, flags=re.IGNORECASE)
        
        # Remove javascript: URLs
        content = re.sub(r'javascript:', '', content, flags=re.IGNORECASE)
        
        # Remove data: URLs that could contain scripts
        content = re.sub(r'data:.*?script.*?base64', '', content, flags=re.IGNORECASE)
        
        return content

# Session security decorator
def secure_session(func):
    """Decorator to ensure session security"""
    def wrapper(*args, **kwargs):
        # Check if session is valid
        if 'authenticated' not in st.session_state or not st.session_state.authenticated:
            st.error("Session not authenticated")
            st.stop()
        
        # Check for session timeout
        if 'login_time' in st.session_state:
            elapsed = datetime.now() - st.session_state.login_time
            if elapsed.total_seconds() > 7200:  # 2 hours
                st.error("Session expired. Please log in again.")
                st.stop()
        
        # Check CSRF token
        if 'csrf_token' not in st.session_state:
            st.error("Invalid session")
            st.stop()
        
        return func(*args, **kwargs)
    
    return wrapper

# Input validation helpers
def validate_input(input_value: Any, input_type: str, **kwargs) -> tuple[bool, Any, str]:
    """Validate various types of input"""
    
    if input_type == "username":
        pattern = r'^[a-zA-Z0-9_-]{3,20}$'
        if not re.match(pattern, str(input_value)):
            return False, None, "Invalid username format"
        return True, input_value, ""
    
    elif input_type == "email":
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, str(input_value)):
            return False, None, "Invalid email format"
        return True, input_value.lower(), ""
    
    elif input_type == "integer":
        try:
            value = int(input_value)
            min_val = kwargs.get('min', float('-inf'))
            max_val = kwargs.get('max', float('inf'))
            if value < min_val or value > max_val:
                return False, None, f"Value must be between {min_val} and {max_val}"
            return True, value, ""
        except ValueError:
            return False, None, "Invalid integer value"
    
    elif input_type == "text":
        max_length = kwargs.get('max_length', 1000)
        if len(str(input_value)) > max_length:
            return False, None, f"Text too long (max {max_length} characters)"
        
        # Sanitize
        sanitized = SecurityMiddleware.sanitize_html(str(input_value))
        return True, sanitized, ""
    
    return False, None, "Unknown input type"