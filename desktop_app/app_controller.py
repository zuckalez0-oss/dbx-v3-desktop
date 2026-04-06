from PyQt5.QtWidgets import QMessageBox

from .auth import AuthAccessDeniedError, AuthService, load_auth_config
from .auth.errors import AuthConfigurationError, AuthSetupRequiredError
from .auth.login_dialog import LoginDialog
from .main_window import MainWindow


class DesktopAppController:
    def __init__(self, app):
        self.app = app
        self.auth_service = None
        self.main_window = None

    def run(self) -> int:
        try:
            self.auth_service = AuthService(load_auth_config())
        except AuthSetupRequiredError as exc:
            QMessageBox.critical(
                None,
                "Configuração de autenticação pendente",
                str(exc),
            )
            return 1
        except AuthConfigurationError as exc:
            QMessageBox.critical(
                None,
                "Falha ao configurar autenticação",
                str(exc),
            )
            return 1

        auth_context = self._restore_or_login()
        if auth_context is None:
            return 0

        self._show_main_window(auth_context)
        return self.app.exec_()

    def _restore_or_login(self):
        try:
            restored_context = self.auth_service.restore_session()
            if restored_context is not None:
                return restored_context
        except AuthAccessDeniedError as exc:
            QMessageBox.warning(None, "Acesso não liberado", str(exc))
        except Exception:
            pass
        return self._open_login_dialog()

    def _open_login_dialog(self):
        login_dialog = LoginDialog(self.auth_service)
        if login_dialog.exec_() == LoginDialog.Accepted:
            return login_dialog.auth_context
        return None

    def _show_main_window(self, auth_context):
        self.main_window = MainWindow(auth_context=auth_context, auth_service=self.auth_service)
        self.main_window.logout_requested.connect(self._handle_logout_requested)
        self.main_window.showMaximized()

    def _handle_logout_requested(self):
        try:
            self.auth_service.sign_out()
        except Exception as exc:
            QMessageBox.warning(
                self.main_window,
                "Logout",
                f"O logout local encontrou um aviso, mas a sessao sera encerrada.\n\nDetalhe: {exc}",
            )

        if self.main_window is not None:
            self.main_window.close()
            self.main_window.deleteLater()
            self.main_window = None

        next_context = self._open_login_dialog()
        if next_context is None:
            self.app.quit()
            return

        self._show_main_window(next_context)
