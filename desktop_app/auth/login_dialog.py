from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QFrame,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from .errors import AuthAccessDeniedError, AuthSessionError


LOGIN_DIALOG_STYLE = """
QDialog {
    background-color: #f4f8fb;
}
QFrame#loginHero {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #103351, stop:1 #1c8f9d);
    border: none;
    border-radius: 16px;
}
QFrame#loginCard {
    background-color: #ffffff;
    border: 1px solid #d8e8f0;
    border-radius: 16px;
}
QLabel#loginEyebrow {
    color: #97f0f4;
    font-size: 9pt;
    font-weight: 700;
    letter-spacing: 0.6px;
}
QLabel#loginTitle {
    color: #ffffff;
    font-size: 18pt;
    font-weight: 800;
}
QLabel#loginSubtitle {
    color: #d8edf4;
    font-size: 9.4pt;
    line-height: 1.4;
}
QLabel#loginHint {
    color: #f4fbff;
    background-color: rgba(255, 255, 255, 0.12);
    border-radius: 10px;
    padding: 10px 12px;
    font-size: 8.8pt;
}
QLabel#formTitle {
    color: #12324b;
    font-size: 14pt;
    font-weight: 800;
}
QLabel#formSubtitle {
    color: #58748a;
    font-size: 9pt;
}
QLabel#feedbackError {
    color: #8f1d1d;
    background-color: #fff1f1;
    border: 1px solid #f0caca;
    border-radius: 10px;
    padding: 8px 10px;
    font-size: 8.8pt;
}
QLabel#feedbackEmpty {
    background: transparent;
    border: none;
    padding: 0px;
}
QLineEdit {
    background-color: #fbfdff;
    border: 1px solid #cfe0ea;
    border-radius: 10px;
    padding: 7px 10px;
    min-height: 18px;
    color: #173b5a;
    font-size: 9pt;
}
QLineEdit:focus {
    border: 1px solid #2ccfd5;
    background-color: #ffffff;
}
QPushButton#primaryButton {
    background-color: #1dc8d0;
    color: #12324b;
    font-weight: 800;
    border-radius: 10px;
    padding: 8px 18px;
    min-height: 18px;
}
QPushButton#primaryButton:hover {
    background-color: #15b8bf;
}
QPushButton#ghostButton {
    background-color: #ffffff;
    color: #406074;
    border: 1px solid #d3e1e8;
    border-radius: 10px;
    padding: 8px 14px;
    min-height: 18px;
}
QPushButton#ghostButton:hover {
    background-color: #f3f8fb;
}
QPushButton#linkButton {
    background-color: transparent;
    color: #0f7e8f;
    border: none;
    padding: 4px 0px;
    font-weight: 700;
}
QPushButton#linkButton:hover {
    color: #0a6572;
}
"""


class LoginDialog(QDialog):
    def __init__(self, auth_service, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.auth_context = None

        self.setWindowTitle("Login DBX-V3")
        self.setModal(True)
        self.setMinimumSize(760, 420)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setStyleSheet(LOGIN_DIALOG_STYLE)
        self._build_ui()

    def _build_ui(self):
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setSpacing(18)

        hero_frame = QFrame()
        hero_frame.setObjectName("loginHero")
        hero_layout = QVBoxLayout(hero_frame)
        hero_layout.setContentsMargins(24, 24, 24, 24)
        hero_layout.setSpacing(14)

        eyebrow = QLabel("DBX-V3 AUTH")
        eyebrow.setObjectName("loginEyebrow")
        hero_layout.addWidget(eyebrow)

        title = QLabel("Acesse o DBX com segurança")
        title.setObjectName("loginTitle")
        title.setWordWrap(True)
        hero_layout.addWidget(title)

        subtitle = QLabel(
            "Faça login com sua conta DBX para liberar o ambiente desktop, restaurar sua sessão e continuar seu fluxo de orçamento e produção sem retrabalho."
        )
        subtitle.setObjectName("loginSubtitle")
        subtitle.setWordWrap(True)
        hero_layout.addWidget(subtitle)

        hint = QLabel(
            "Dica: o nome exibido no aplicativo seguirá o nick ou nome de usuário configurado para a sua conta. "
            "Se sua conta já foi criada, use email e senha normalmente."
        )
        hint.setObjectName("loginHint")
        hint.setWordWrap(True)
        hero_layout.addWidget(hint)
        hero_layout.addStretch(1)

        card_frame = QFrame()
        card_frame.setObjectName("loginCard")
        card_layout = QVBoxLayout(card_frame)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(12)

        form_title = QLabel("Entrar no aplicativo")
        form_title.setObjectName("formTitle")
        card_layout.addWidget(form_title)

        form_subtitle = QLabel(
            "Use o email e a senha da sua conta para liberar o uso do DBX-V3."
        )
        form_subtitle.setObjectName("formSubtitle")
        form_subtitle.setWordWrap(True)
        card_layout.addWidget(form_subtitle)

        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignTop)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("voce@empresa.com")
        self.email_input.setMinimumHeight(34)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Digite sua senha")
        self.password_input.setMinimumHeight(34)

        form_layout.addRow("Email:", self.email_input)
        form_layout.addRow("Senha:", self.password_input)
        card_layout.addLayout(form_layout)

        self.feedback_label = QLabel("")
        self.feedback_label.setObjectName("feedbackEmpty")
        self.feedback_label.setWordWrap(True)
        self.feedback_label.hide()
        card_layout.addWidget(self.feedback_label)

        self.reset_password_btn = QPushButton("Esqueci Minha Senha")
        self.reset_password_btn.setObjectName("linkButton")
        card_layout.addWidget(self.reset_password_btn, 0, Qt.AlignLeft)

        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)
        actions_layout.addStretch(1)

        self.cancel_btn = QPushButton("Fechar")
        self.cancel_btn.setObjectName("ghostButton")
        self.login_btn = QPushButton("Entrar")
        self.login_btn.setObjectName("primaryButton")

        actions_layout.addWidget(self.cancel_btn)
        actions_layout.addWidget(self.login_btn)
        card_layout.addLayout(actions_layout)

        root_layout.addWidget(hero_frame, 5)
        root_layout.addWidget(card_frame, 6)

        self.login_btn.clicked.connect(self._handle_login)
        self.cancel_btn.clicked.connect(self.reject)
        self.reset_password_btn.clicked.connect(self._handle_password_reset)
        self.password_input.returnPressed.connect(self._handle_login)
        self.email_input.returnPressed.connect(self._focus_password)

    def _focus_password(self):
        self.password_input.setFocus()

    def _set_busy_state(self, busy: bool):
        self.login_btn.setEnabled(not busy)
        self.cancel_btn.setEnabled(not busy)
        self.reset_password_btn.setEnabled(not busy)
        self.email_input.setEnabled(not busy)
        self.password_input.setEnabled(not busy)

    def _show_feedback(self, message: str):
        normalized_message = (message or "").strip()
        if not normalized_message:
            self.feedback_label.clear()
            self.feedback_label.setObjectName("feedbackEmpty")
            self.feedback_label.hide()
        else:
            self.feedback_label.setText(normalized_message)
            self.feedback_label.setObjectName("feedbackError")
            self.feedback_label.show()
        self.feedback_label.style().unpolish(self.feedback_label)
        self.feedback_label.style().polish(self.feedback_label)

    def _handle_login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text()
        self._show_feedback("")
        self._set_busy_state(True)

        try:
            self.auth_context = self.auth_service.sign_in(email, password)
            self.accept()
        except AuthAccessDeniedError as exc:
            self._show_feedback(str(exc))
        except AuthSessionError as exc:
            self._show_feedback(str(exc))
        except Exception as exc:
            self._show_feedback(f"Erro inesperado no login: {exc}")
        finally:
            self._set_busy_state(False)

    def _handle_password_reset(self):
        email = self.email_input.text().strip()
        try:
            self.auth_service.request_password_reset(email)
            QMessageBox.information(
                self,
                "Recuperação de senha",
                "Se o email estiver cadastrado, o fluxo de redefinição foi iniciado com sucesso.",
            )
        except AuthSessionError as exc:
            QMessageBox.warning(self, "Falha na recuperação", str(exc))
