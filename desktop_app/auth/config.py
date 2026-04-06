import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from app_paths import get_app_data_dir

from .errors import AuthSetupRequiredError


AUTH_DIRNAME = "auth"
AUTH_CONFIG_FILENAME = "supabase_config.json"


@dataclass
class AuthConfig:
    supabase_url: str
    supabase_anon_key: str
    profiles_table: str = "profiles"
    profile_lookup_column: str = "id"
    require_dbx_access_claim: bool = True
    require_profile: bool = False
    desktop_access_column: str = "desktop_access"
    status_column: str = "status"
    allowed_statuses: list[str] = field(default_factory=lambda: ["active", "trial"])


def get_auth_dir() -> Path:
    auth_dir = get_app_data_dir() / AUTH_DIRNAME
    auth_dir.mkdir(parents=True, exist_ok=True)
    return auth_dir


def get_auth_config_path() -> Path:
    return get_auth_dir() / AUTH_CONFIG_FILENAME


def _write_sample_config_if_missing(config_path: Path):
    if config_path.exists():
        return

    sample_payload = {
        "supabase_url": "https://SEU-PROJETO.supabase.co",
        "supabase_anon_key": "COLE_A_ANON_KEY_AQUI",
        "profiles_table": "profiles",
        "profile_lookup_column": "id",
        "require_dbx_access_claim": True,
        "require_profile": False,
        "desktop_access_column": "desktop_access",
        "status_column": "status",
        "allowed_statuses": ["active", "trial"],
    }
    config_path.write_text(
        json.dumps(sample_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _read_file_config(config_path: Path) -> dict:
    if not config_path.exists():
        return {}
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _env_bool(name: str, default: bool) -> bool:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _merge_config_value(file_config: dict, env_name: str, file_key: str, default=None):
    return os.environ.get(env_name, file_config.get(file_key, default))


def _looks_like_placeholder(value: str) -> bool:
    normalized = (value or "").strip().lower()
    placeholder_markers = [
        "seu-projeto",
        "cole_a_anon_key_aqui",
        "your-project",
        "your-anon-key",
        "example",
    ]
    return any(marker in normalized for marker in placeholder_markers)


def _validate_auth_config_values(config_path: Path, supabase_url: str, supabase_anon_key: str):
    if _looks_like_placeholder(supabase_url) or _looks_like_placeholder(supabase_anon_key):
        raise AuthSetupRequiredError(
            "O arquivo de configuracao de acesso do DBX ainda esta com valores de exemplo.\n\n"
            f"Atualize o arquivo abaixo com a URL real do projeto e a chave publica:\n{config_path}"
        )

    parsed_url = urlparse(supabase_url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise AuthSetupRequiredError(
            "A URL do servico de autenticacao esta invalida.\n\n"
            "Use o formato: https://SEU-PROJETO.supabase.co\n\n"
            f"Arquivo: {config_path}"
        )


def load_auth_config() -> AuthConfig:
    config_path = get_auth_config_path()
    _write_sample_config_if_missing(config_path)
    file_config = _read_file_config(config_path)

    supabase_url = _merge_config_value(file_config, "SUPABASE_URL", "supabase_url", "").strip()
    supabase_anon_key = _merge_config_value(
        file_config,
        "SUPABASE_ANON_KEY",
        "supabase_anon_key",
        "",
    ).strip()

    if not supabase_url or not supabase_anon_key:
        raise AuthSetupRequiredError(
            "A autenticacao do DBX ainda nao foi configurada.\n\n"
            "Preencha SUPABASE_URL e SUPABASE_ANON_KEY via variaveis de ambiente "
            f"ou no arquivo:\n{config_path}"
        )

    _validate_auth_config_values(config_path, supabase_url, supabase_anon_key)

    allowed_statuses_raw = _merge_config_value(
        file_config,
        "DBX_AUTH_ALLOWED_STATUSES",
        "allowed_statuses",
        ["active", "trial"],
    )
    if isinstance(allowed_statuses_raw, str):
        allowed_statuses = [item.strip() for item in allowed_statuses_raw.split(",") if item.strip()]
    else:
        allowed_statuses = [str(item).strip() for item in (allowed_statuses_raw or []) if str(item).strip()]

    return AuthConfig(
        supabase_url=supabase_url,
        supabase_anon_key=supabase_anon_key,
        profiles_table=str(
            _merge_config_value(file_config, "DBX_AUTH_PROFILES_TABLE", "profiles_table", "profiles")
        ).strip(),
        profile_lookup_column=str(
            _merge_config_value(file_config, "DBX_AUTH_PROFILE_LOOKUP_COLUMN", "profile_lookup_column", "id")
        ).strip(),
        require_dbx_access_claim=_env_bool(
            "DBX_AUTH_REQUIRE_DBX_ACCESS_CLAIM",
            bool(file_config.get("require_dbx_access_claim", True)),
        ),
        require_profile=_env_bool(
            "DBX_AUTH_REQUIRE_PROFILE",
            bool(file_config.get("require_profile", False)),
        ),
        desktop_access_column=str(
            _merge_config_value(
                file_config,
                "DBX_AUTH_DESKTOP_ACCESS_COLUMN",
                "desktop_access_column",
                "desktop_access",
            )
        ).strip(),
        status_column=str(
            _merge_config_value(file_config, "DBX_AUTH_STATUS_COLUMN", "status_column", "status")
        ).strip(),
        allowed_statuses=allowed_statuses or ["active"],
    )
