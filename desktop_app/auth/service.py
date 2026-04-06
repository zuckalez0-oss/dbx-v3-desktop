from __future__ import annotations

from .client import create_supabase_client
from .config import AuthConfig
from .errors import AuthAccessDeniedError, AuthSessionError
from .models import AuthenticatedUserContext, SessionTokens
from .session_store import SessionStore


class AuthService:
    def __init__(self, config: AuthConfig, session_store: SessionStore | None = None):
        self.config = config
        self.session_store = session_store or SessionStore()

    def restore_session(self) -> AuthenticatedUserContext | None:
        stored_tokens = self.session_store.load()
        if stored_tokens is None:
            return None

        client = create_supabase_client(self.config)
        try:
            response = client.auth.set_session(stored_tokens.access_token, stored_tokens.refresh_token)
            session = self._extract_session(response) or stored_tokens
            user = self._fetch_verified_user(client)
            context = self._build_authenticated_context(client, user)
            self.session_store.save(self._session_tokens_from_session(session, user))
            return context
        except AuthAccessDeniedError:
            self._clear_session_safely()
            raise
        except Exception:
            self._clear_session_safely()
            return None

    def sign_in(self, email: str, password: str) -> AuthenticatedUserContext:
        normalized_email = (email or "").strip()
        if not normalized_email or not password:
            raise AuthSessionError("Informe email e senha para continuar.")

        client = create_supabase_client(self.config)
        try:
            response = client.auth.sign_in_with_password(
                {
                    "email": normalized_email,
                    "password": password,
                }
            )
            session = self._extract_session(response)
            if session is None:
                raise AuthSessionError(
                    "Nao foi possivel concluir o login com os dados retornados pelo servico de autenticacao."
                )
            user = self._fetch_verified_user(client)
            context = self._build_authenticated_context(client, user)
            self.session_store.save(self._session_tokens_from_session(session, user))
            return context
        except AuthAccessDeniedError:
            self._clear_session_safely()
            raise
        except Exception as exc:
            self._clear_session_safely()
            raise AuthSessionError(f"Falha ao autenticar: {exc}") from exc

    def request_password_reset(self, email: str):
        normalized_email = (email or "").strip()
        if not normalized_email:
            raise AuthSessionError("Informe o email para recuperar a senha.")

        client = create_supabase_client(self.config)
        try:
            client.auth.reset_password_for_email(normalized_email)
        except Exception as exc:
            raise AuthSessionError(f"Nao foi possivel iniciar a recuperacao de senha: {exc}") from exc

    def sign_out(self):
        stored_tokens = None
        try:
            stored_tokens = self.session_store.load()
        except AuthSessionError:
            stored_tokens = None

        try:
            if stored_tokens is not None:
                client = create_supabase_client(self.config)
                try:
                    client.auth.set_session(stored_tokens.access_token, stored_tokens.refresh_token)
                except Exception:
                    pass
                try:
                    client.auth.sign_out()
                except Exception:
                    pass
        finally:
            self._clear_session_safely()

    def _fetch_verified_user(self, client):
        response = client.auth.get_user()
        user = self._extract_user(response)
        if user is None:
            raise AuthSessionError("Nao foi possivel validar o usuario autenticado no servidor de acesso.")
        return user

    def _build_authenticated_context(self, client, user) -> AuthenticatedUserContext:
        app_metadata = self._as_dict(self._get_entity_value(user, "app_metadata", {}))
        user_metadata = self._as_dict(self._get_entity_value(user, "user_metadata", {}))
        profile = self._load_profile(client, self._get_entity_value(user, "id", ""))

        if self.config.require_dbx_access_claim and not bool(app_metadata.get("dbx_access")):
            raise AuthAccessDeniedError(
                "Seu usuario autenticou com sucesso, mas ainda nao foi liberado para usar o DBX.\n\n"
                "Solicite a liberacao ao administrador."
            )

        if profile:
            desktop_access_value = profile.get(self.config.desktop_access_column)
            if desktop_access_value is False:
                raise AuthAccessDeniedError(
                    "Seu acesso ao desktop DBX esta bloqueado no cadastro de perfil."
                )

            raw_status = str(profile.get(self.config.status_column, "") or "").strip().lower()
            if raw_status and self.config.allowed_statuses and raw_status not in self.config.allowed_statuses:
                raise AuthAccessDeniedError(
                    "Seu cadastro existe, mas o status atual nao permite acesso ao DBX."
                )
        elif self.config.require_profile:
            raise AuthAccessDeniedError(
                "Seu usuario autenticou, mas nao possui perfil operacional configurado para o DBX."
            )

        roles = app_metadata.get("roles", [])
        if isinstance(roles, str):
            roles = [roles]
        elif not isinstance(roles, list):
            roles = []

        email = str(self._get_entity_value(user, "email", "") or "")
        display_name = self._resolve_user_display_name(profile, user_metadata, app_metadata, email)

        return AuthenticatedUserContext(
            user_id=str(self._get_entity_value(user, "id", "") or ""),
            email=email,
            display_name=display_name,
            app_metadata=app_metadata,
            user_metadata=user_metadata,
            profile=profile,
            roles=[str(role) for role in roles],
        )

    def _resolve_user_display_name(self, profile: dict, user_metadata: dict, app_metadata: dict, email: str) -> str:
        return self._pick_first_text(
            profile.get("username"),
            profile.get("nickname"),
            profile.get("nick"),
            profile.get("display_name"),
            user_metadata.get("username"),
            user_metadata.get("nickname"),
            user_metadata.get("nick"),
            user_metadata.get("user_name"),
            user_metadata.get("display_name"),
            user_metadata.get("full_name"),
            app_metadata.get("username"),
            app_metadata.get("nickname"),
            app_metadata.get("nick"),
            email,
        )

    def _load_profile(self, client, user_id: str) -> dict:
        if not user_id:
            return {}
        try:
            response = (
                client.table(self.config.profiles_table)
                .select("*")
                .eq(self.config.profile_lookup_column, user_id)
                .limit(1)
                .execute()
            )
            data = getattr(response, "data", None)
            if isinstance(data, list) and data:
                return self._as_dict(data[0])
            if isinstance(data, dict):
                return self._as_dict(data)
            return {}
        except Exception:
            if self.config.require_profile:
                raise
            return {}

    def _extract_session(self, response):
        direct_session = self._get_entity_value(response, "session")
        if direct_session is not None:
            return direct_session
        data = self._get_entity_value(response, "data")
        return self._get_entity_value(data, "session")

    def _extract_user(self, response):
        direct_user = self._get_entity_value(response, "user")
        if direct_user is not None:
            return direct_user
        data = self._get_entity_value(response, "data")
        return self._get_entity_value(data, "user")

    def _session_tokens_from_session(self, session, user) -> SessionTokens:
        return SessionTokens(
            access_token=str(self._get_entity_value(session, "access_token", "") or ""),
            refresh_token=str(self._get_entity_value(session, "refresh_token", "") or ""),
            token_type=str(self._get_entity_value(session, "token_type", "bearer") or "bearer"),
            expires_at=self._coerce_int(self._get_entity_value(session, "expires_at")),
            expires_in=self._coerce_int(self._get_entity_value(session, "expires_in")),
            user_id=str(self._get_entity_value(user, "id", "") or ""),
            email=str(self._get_entity_value(user, "email", "") or ""),
        )

    def _coerce_int(self, value):
        if value in (None, ""):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _clear_session_safely(self):
        try:
            self.session_store.clear()
        except AuthSessionError:
            pass

    def _get_entity_value(self, entity, key: str, default=None):
        if entity is None:
            return default
        if isinstance(entity, dict):
            return entity.get(key, default)
        return getattr(entity, key, default)

    def _as_dict(self, value) -> dict:
        if isinstance(value, dict):
            return value
        if value is None:
            return {}
        if hasattr(value, "__dict__"):
            return {
                key: attr_value
                for key, attr_value in vars(value).items()
                if not key.startswith("_")
            }
        return {}

    def _pick_first_text(self, *values) -> str:
        for value in values:
            text = str(value or "").strip()
            if text:
                return text
        return ""
