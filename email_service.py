import logging
import os
from html import escape

from dotenv import load_dotenv
from fastapi_mail import (
    FastMail,
    ConnectionConfig,
    MessageSchema,
    MessageType,
)

load_dotenv()

logger = logging.getLogger(__name__)

mail_config = ConnectionConfig(
    MAIL_USERNAME=os.environ["MAIL_USERNAME"],
    MAIL_PASSWORD=os.environ["MAIL_PASSWORD"],
    MAIL_FROM=os.environ["MAIL_FROM"],
    MAIL_FROM_NAME="HAGORA",
    MAIL_PORT=int(os.getenv("MAIL_PORT", "587")),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TIMEOUT=30,
)


async def send_reset_email(email: str, token: str) -> bool:
    """Send the password reset email.

    Runs inside a FastAPI BackgroundTask, so an exception here would
    otherwise vanish silently. We log it instead and return True/False.
    """
    frontend_url = os.getenv(
        "FRONTEND_URL",
        "http://localhost:5173",
    ).rstrip("/")

    reset_link = f"{frontend_url}/reset-password?token={token}"

    safe_link = escape(reset_link, quote=True)

    html_body = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reset Your Password</title>
    </head>
    <body style="margin:0; padding:0; background-color:#fff5f7;
                 font-family:Arial,Helvetica,sans-serif; color:#333333;">
        <table role="presentation" width="100%" cellspacing="0"
               cellpadding="0" style="background-color:#fff5f7; padding:32px 12px;">
            <tr>
                <td align="center">
                    <table role="presentation" width="100%" cellspacing="0"
                           cellpadding="0"
                           style="max-width:560px; background-color:#ffffff;
                                  border-radius:16px; overflow:hidden;">
                        <tr>
                            <td align="center"
                                style="background-color:#e879a9; padding:28px 20px;">
                                <h1 style="margin:0; color:#ffffff;
                                           font-size:30px; letter-spacing:3px;">
                                    HAGORA
                                </h1>
                                <p style="margin:8px 0 0; color:#ffffff;
                                          font-size:14px;">
                                    Beauty begins with you
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding:32px 28px;">
                                <h2 style="margin:0 0 18px; color:#292929;
                                           font-size:23px;">
                                    Reset Your Password
                                </h2>

                                <p style="font-size:15px; line-height:1.7;">
                                    Hello,
                                </p>

                                <p style="font-size:15px; line-height:1.7;">
                                    We received a request to reset your HAGORA
                                    account password. Click the button below
                                    to choose a new password.
                                </p>

                                <table role="presentation" cellspacing="0"
                                       cellpadding="0" style="margin:28px auto;">
                                    <tr>
                                        <td align="center"
                                            bgcolor="#e879a9"
                                            style="border-radius:8px;">
                                            <a href="{safe_link}"
                                               style="display:inline-block;
                                                      padding:14px 28px;
                                                      color:#ffffff;
                                                      text-decoration:none;
                                                      font-size:15px;
                                                      font-weight:bold;">
                                                Reset Password
                                            </a>
                                        </td>
                                    </tr>
                                </table>

                                <p style="font-size:13px; line-height:1.7;
                                          color:#666666;">
                                    This link expires in 15 minutes.
                                    If you did not request a password reset,
                                    you can safely ignore this email.
                                </p>

                                <hr style="border:0; border-top:1px solid #eeeeee;
                                           margin:26px 0;">

                                <p style="font-size:12px; line-height:1.6;
                                          color:#888888;">
                                    If the button doesn't work, copy this link
                                    into your browser:
                                </p>

                                <p style="font-size:12px; line-height:1.6;
                                          word-break:break-all;">
                                    <a href="{safe_link}"
                                       style="color:#c34f83;">
                                        {safe_link}
                                    </a>
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <td align="center"
                                style="background-color:#fff0f5; padding:18px;">
                                <p style="margin:0; color:#888888;
                                          font-size:12px;">
                                    © HAGORA. All rights reserved.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    plain_body = (
        "HAGORA - Reset Your Password\n\n"
        "We received a request to reset your HAGORA password.\n\n"
        f"Open this link to choose a new password:\n{reset_link}\n\n"
        "This link expires in 15 minutes.\n"
        "If you did not request this, you can ignore this email."
    )

    message = MessageSchema(
        subject="HAGORA - Reset Your Password",
        recipients=[email],
        body=html_body,
        subtype=MessageType.html,
        alternative_body=plain_body,
    )

    try:
        mailer = FastMail(mail_config)
        await mailer.send_message(message)
    except Exception:
        # Full traceback goes to the server log (Gmail auth error,
        # timeout, wrong App Password, etc.)
        logger.exception("Failed to send reset email to %s", email)
        return False

    logger.info("Reset email sent to %s", email)
    return True