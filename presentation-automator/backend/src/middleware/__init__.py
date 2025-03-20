"""
Middleware components for the Presentation Automator API.
Includes authentication, error handling, and other request processing functionality.
"""

from .auth import get_current_user, create_access_token, verify_password, get_password_hash
from .error_handler import register_exception_handlers 