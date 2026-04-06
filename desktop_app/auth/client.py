from typing import Any

from .config import AuthConfig
from .errors import AuthConfigurationError

try:
    from supabase import Client, create_client

    SUPABASE_IMPORT_ERROR = None
except Exception as exc:  # pragma: no cover - depende da lib em runtime
    Client = Any
    create_client = None
    SUPABASE_IMPORT_ERROR = exc


def create_supabase_client(config: AuthConfig) -> Client:
    if create_client is None:
        raise AuthConfigurationError(
            "A biblioteca 'supabase' nao esta instalada ou falhou ao carregar.\n\n"
            f"Erro original: {SUPABASE_IMPORT_ERROR}"
        )
    return create_client(config.supabase_url, config.supabase_anon_key)
