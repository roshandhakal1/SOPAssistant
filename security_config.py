"""
Security Configuration for SOP Assistant
Corporate-grade security settings and policies
"""

import os
from typing import Dict, List

class SecurityConfig:
    """Security configuration and policies"""
    
    # Authentication Settings
    PASSWORD_MIN_LENGTH = 12
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_NUMBERS = True
    PASSWORD_REQUIRE_SPECIAL = True
    PASSWORD_HISTORY_COUNT = 10  # Remember last N passwords
    PASSWORD_EXPIRY_DAYS = 90
    
    # Session Settings
    SESSION_TIMEOUT_MINUTES = 120  # 2 hours
    SESSION_ABSOLUTE_TIMEOUT_MINUTES = 480  # 8 hours max
    REMEMBER_ME_DISABLED = True  # Disabled for security
    CONCURRENT_SESSIONS_ALLOWED = False
    
    # Rate Limiting
    LOGIN_MAX_ATTEMPTS = 5
    LOGIN_LOCKOUT_MINUTES = 30
    API_RATE_LIMIT_PER_MINUTE = 60
    FILE_UPLOAD_RATE_LIMIT_PER_HOUR = 100
    
    # File Upload Security
    MAX_FILE_SIZE_MB = 50
    ALLOWED_FILE_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt', '.csv', '.md'}
    SCAN_UPLOADS_FOR_MALWARE = True
    QUARANTINE_SUSPICIOUS_FILES = True
    
    # Encryption Settings
    ENCRYPTION_ALGORITHM = "AES-256-GCM"
    KEY_DERIVATION_FUNCTION = "PBKDF2"
    KEY_DERIVATION_ITERATIONS = 100000
    
    # Network Security
    FORCE_HTTPS = True
    HSTS_ENABLED = True
    HSTS_MAX_AGE = 31536000  # 1 year
    
    # Content Security Policy
    CSP_POLICY = {
        "default-src": ["'self'"],
        "script-src": ["'self'", "'unsafe-inline'", "'unsafe-eval'", "https://cdn.jsdelivr.net"],
        "style-src": ["'self'", "'unsafe-inline'"],
        "img-src": ["'self'", "data:", "https:"],
        "font-src": ["'self'", "https://fonts.gstatic.com"],
        "connect-src": ["'self'", "https://api.anthropic.com", "https://generativelanguage.googleapis.com"],
        "frame-ancestors": ["'none'"],
        "form-action": ["'self'"],
        "base-uri": ["'self'"]
    }
    
    # Security Headers
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        "Cache-Control": "no-store, no-cache, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }
    
    # Audit Settings
    AUDIT_LOG_ENABLED = True
    AUDIT_LOG_FILE = "security_audit.log"
    AUDIT_LOG_ROTATION = "daily"
    AUDIT_LOG_RETENTION_DAYS = 90
    AUDIT_EVENTS = [
        "login_success",
        "login_failure",
        "logout",
        "password_change",
        "user_created",
        "user_modified",
        "user_deleted",
        "file_upload",
        "file_download",
        "admin_action",
        "suspicious_activity",
        "rate_limit_exceeded",
        "session_timeout"
    ]
    
    # Data Protection
    ENCRYPT_DATA_AT_REST = True
    ENCRYPT_DATA_IN_TRANSIT = True
    PII_DETECTION_ENABLED = True
    PII_REDACTION_ENABLED = True
    DATA_RETENTION_DAYS = 365
    
    # Input Validation
    MAX_INPUT_LENGTH = 2000
    SANITIZE_HTML_INPUT = True
    BLOCK_COMMON_EXPLOITS = True
    SQL_INJECTION_PROTECTION = True
    XSS_PROTECTION = True
    
    # API Security
    API_KEY_REQUIRED = True
    API_KEY_ROTATION_DAYS = 90
    OAUTH_ENABLED = True
    OAUTH_PROVIDERS = ["google"]
    
    # Monitoring and Alerting
    SECURITY_MONITORING_ENABLED = True
    ALERT_ON_SUSPICIOUS_ACTIVITY = True
    ALERT_EMAIL = os.getenv("SECURITY_ALERT_EMAIL", "security@company.com")
    ALERT_THRESHOLD_LOGIN_FAILURES = 3
    ALERT_THRESHOLD_RATE_LIMIT = 10
    
    # Compliance
    GDPR_COMPLIANT = True
    CCPA_COMPLIANT = True
    SOC2_COMPLIANT = True
    HIPAA_COMPLIANT = False  # Set to True if handling health data
    
    # Development vs Production
    IS_PRODUCTION = os.getenv("ENVIRONMENT", "development") == "production"
    DEBUG_MODE = not IS_PRODUCTION
    VERBOSE_ERRORS = not IS_PRODUCTION
    
    @classmethod
    def get_csp_header(cls) -> str:
        """Generate Content Security Policy header"""
        policies = []
        for directive, sources in cls.CSP_POLICY.items():
            policy = f"{directive} {' '.join(sources)}"
            policies.append(policy)
        return "; ".join(policies)
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """Validate security configuration"""
        warnings = []
        
        if not cls.IS_PRODUCTION and cls.FORCE_HTTPS:
            warnings.append("HTTPS enforcement is enabled in development mode")
        
        if cls.PASSWORD_MIN_LENGTH < 12:
            warnings.append("Password minimum length should be at least 12 characters")
        
        if cls.SESSION_TIMEOUT_MINUTES > 240:
            warnings.append("Session timeout is longer than recommended 4 hours")
        
        if not cls.AUDIT_LOG_ENABLED:
            warnings.append("Audit logging is disabled - this is not recommended for production")
        
        if cls.DEBUG_MODE and cls.IS_PRODUCTION:
            warnings.append("DEBUG mode is enabled in production - this is a security risk")
        
        return warnings

# Environment-specific overrides
if os.getenv("ENVIRONMENT") == "development":
    SecurityConfig.FORCE_HTTPS = False
    SecurityConfig.SESSION_TIMEOUT_MINUTES = 480  # 8 hours for development
    SecurityConfig.LOGIN_MAX_ATTEMPTS = 10
    SecurityConfig.VERBOSE_ERRORS = True