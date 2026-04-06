"""Camada de autenticação do desktop baseada em Supabase Auth."""

from .config import AuthConfig, load_auth_config
from .errors import (
    AuthAccessDeniedError,
    AuthConfigurationError,
    AuthSessionError,
    AuthSetupRequiredError,
)
from .models import AuthenticatedUserContext, SessionTokens
from .service import AuthService

__all__ = [
    "AuthConfig",
    "AuthenticatedUserContext",
    "AuthAccessDeniedError",
    "AuthConfigurationError",
    "AuthSessionError",
    "AuthSetupRequiredError",
    "AuthService",
    "SessionTokens",
    "load_auth_config",
]
