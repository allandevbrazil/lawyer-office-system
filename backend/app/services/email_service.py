from app.core.config import Settings


class EmailService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def send(self, *, recipient: str, subject: str, body: str, html: str | None = None) -> None:
        if not self.settings.resend_api_key or not self.settings.resend_from_email:
            print(f"[email-console] to={recipient} subject={subject}\n{body}\n{html or ''}")
            return

        import resend

        resend.api_key = self.settings.resend_api_key
        resend.Emails.send(
            {
                "from": self.settings.resend_from_email,
                "to": [recipient],
                "subject": subject,
                "text": body,
                "html": html or body,
            }
        )
