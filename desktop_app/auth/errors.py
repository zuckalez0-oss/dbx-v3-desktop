class AuthError(Exception):
    """Base para erros da camada de autenticação."""


class AuthConfigurationError(AuthError):
    """Configuração ausente ou inválida para Supabase Auth."""


class AuthSetupRequiredError(AuthConfigurationError):
    """A aplicação precisa de configuração inicial antes de autenticar."""


class AuthSessionError(AuthError):
    """Falha ao criar, restaurar ou persistir sessão."""


class AuthAccessDeniedError(AuthError):
    """Usuário autenticado, porém sem autorização para usar o DBX."""
