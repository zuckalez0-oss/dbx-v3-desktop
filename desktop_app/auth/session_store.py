import json
from pathlib import Path

from .config import get_auth_dir
from .errors import AuthSessionError
from .models import SessionTokens

try:
    import win32crypt

    DPAPI_AVAILABLE = True
except ImportError:
    win32crypt = None
    DPAPI_AVAILABLE = False


class SessionStore:
    def __init__(self, session_path: Path | None = None):
        self.session_path = session_path or (get_auth_dir() / "session.bin")

    def load(self) -> SessionTokens | None:
        if not self.session_path.exists():
            return None
        try:
            encrypted_payload = self.session_path.read_bytes()
            decrypted_payload = self._decrypt(encrypted_payload)
            payload = json.loads(decrypted_payload.decode("utf-8"))
            return SessionTokens(**payload)
        except Exception as exc:
            raise AuthSessionError(f"Nao foi possivel restaurar a sessao local: {exc}") from exc

    def save(self, session_tokens: SessionTokens):
        try:
            payload = json.dumps(session_tokens.__dict__, ensure_ascii=False).encode("utf-8")
            encrypted_payload = self._encrypt(payload)
            self.session_path.parent.mkdir(parents=True, exist_ok=True)
            self.session_path.write_bytes(encrypted_payload)
        except Exception as exc:
            raise AuthSessionError(f"Nao foi possivel salvar a sessao local: {exc}") from exc

    def clear(self):
        try:
            if self.session_path.exists():
                self.session_path.unlink()
        except OSError as exc:
            raise AuthSessionError(f"Nao foi possivel limpar a sessao local: {exc}") from exc

    def _encrypt(self, raw_data: bytes) -> bytes:
        if not DPAPI_AVAILABLE:
            raise AuthSessionError(
                "pywin32 nao esta disponivel. A persistencia segura da sessao via Windows DPAPI requer essa dependencia."
            )
        return win32crypt.CryptProtectData(raw_data, "DBX-V3 Session", None, None, None, 0)

    def _decrypt(self, encrypted_data: bytes) -> bytes:
        if not DPAPI_AVAILABLE:
            raise AuthSessionError(
                "pywin32 nao esta disponivel. A leitura segura da sessao via Windows DPAPI requer essa dependencia."
            )
        return win32crypt.CryptUnprotectData(encrypted_data, None, None, None, 0)[1]
