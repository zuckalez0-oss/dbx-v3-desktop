from dataclasses import dataclass, field


@dataclass
class SessionTokens:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_at: int | None = None
    expires_in: int | None = None
    user_id: str = ""
    email: str = ""


@dataclass
class AuthenticatedUserContext:
    user_id: str
    email: str
    display_name: str
    app_metadata: dict = field(default_factory=dict)
    user_metadata: dict = field(default_factory=dict)
    profile: dict = field(default_factory=dict)
    roles: list[str] = field(default_factory=list)
