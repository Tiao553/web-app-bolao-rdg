from __future__ import annotations

from app.core.config import get_settings


class EmailService:
    """Serviço de envio de emails usando Resend."""

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = (
            settings.resend_api_key.get_secret_value()
            if settings.resend_api_key
            else None
        )
        self._from_addr = settings.email_from or "Bolão RDG <onboarding@resend.dev>"
        self._frontend_url = settings.frontend_url or "http://localhost:3000"

    def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """Envia email de recuperação de senha."""
        reset_url = f"{self._frontend_url}/reset-password?token={reset_token}"

        subject = "Recuperação de senha — Bolão Copa RDG"
        html_body = self._build_reset_email_html(reset_url)
        text_body = self._build_reset_email_text(reset_url)

        return self._send_email(to_email, subject, html_body, text_body)

    def _build_reset_email_html(self, reset_url: str) -> str:
        return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: 'Inter', -apple-system, sans-serif; background: #09090B; margin: 0; padding: 40px 20px;">
    <div style="max-width: 560px; margin: 0 auto; background: #0F0F12; border: 1px solid #27272D; border-radius: 24px; padding: 40px;">
        
        <!-- Logo -->
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 32px;">
            <div style="width: 44px; height: 44px; border-radius: 12px; background: linear-gradient(135deg, #F97316, #EA580C); display: grid; place-items: center; color: white; font-weight: 800; font-size: 16px;">R</div>
            <div>
                <div style="color: #E8E8EA; font-weight: 700; font-size: 16px;">Copa RDG</div>
                <div style="color: #71717A; font-size: 10px; text-transform: uppercase; letter-spacing: 0.1em; font-family: monospace;">Bolão oficial</div>
            </div>
        </div>

        <!-- Conteúdo -->
        <h1 style="color: #E8E8EA; font-size: 24px; font-weight: 800; margin: 0 0 16px; letter-spacing: -0.02em;">
            Recuperação de senha
        </h1>
        
        <p style="color: #A1A1AA; font-size: 15px; line-height: 1.6; margin: 0 0 24px;">
            Olá! Recebemos uma solicitação para redefinir sua senha do Bolão Copa RDG.
        </p>

        <!-- Botão -->
        <a href="{reset_url}" style="display: inline-block; background: linear-gradient(135deg, #F97316, #EA580C); color: white; font-size: 14px; font-weight: 800; text-decoration: none; padding: 16px 32px; border-radius: 14px; box-shadow: 0 18px 34px rgba(249,115,22,0.26);">
            Redefinir minha senha →
        </a>

        <!-- Info -->
        <p style="color: #71717A; font-size: 13px; line-height: 1.6; margin: 24px 0 0;">
            Este link expira em <strong style="color: #A1A1AA;">1 hora</strong>.
        </p>

        <hr style="border: none; border-top: 1px solid #27272D; margin: 32px 0;">

        <!-- Footer -->
        <p style="color: #71717A; font-size: 12px; line-height: 1.6; margin: 0;">
            Se você não solicitou esta alteração, pode ignorar este email com segurança.
        </p>

    </div>
</body>
</html>
"""

    def _build_reset_email_text(self, reset_url: str) -> str:
        return f"""
Recuperação de senha — Bolão Copa RDG

Olá!

Recebemos uma solicitação para redefinir sua senha.

Clique no link abaixo para criar uma nova senha:
{reset_url}

Este link expira em 1 hora.

Se você não solicitou esta alteração, ignore este email.

— Equipe Bolão RDG
"""

    def _send_email(
        self, to: str, subject: str, html: str, text: str
    ) -> bool:
        """Envia email usando Resend API."""
        # Modo desenvolvimento: se não tem API key, apenas loga
        if not self._api_key:
            reset_url = html.split('href="')[1].split('"')[0] if 'href="' in html else "URL not found"
            self._log_dev_email(to, subject, reset_url)
            return True

        try:
            import resend

            resend.api_key = self._api_key

            resend.Emails.send(
                {
                    "from": self._from_addr,
                    "to": [to],
                    "subject": subject,
                    "html": html,
                    "text": text,
                }
            )
            return True
        except Exception as e:
            # Em caso de erro (ex: domínio não verificado), log o link como fallback
            print(f"Erro ao enviar email: {e}")
            reset_url = html.split('href="')[1].split('"')[0] if 'href="' in html else "URL not found"
            self._log_dev_email(to, subject, reset_url)
            return False

    def _log_dev_email(self, to: str, subject: str, reset_url: str) -> None:
        """Loga informações do email no console para desenvolvimento."""
        print(f"\n{'='*60}")
        print(f"[DEV] Email para: {to}")
        print(f"[DEV] Assunto: {subject}")
        print(f"[DEV] Link de reset: {reset_url}")
        print(f"{'='*60}\n")
