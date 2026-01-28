import os
import smtplib
from email.mime.text import MIMEText

def send_email(to_email: str, subject: str, body: str):
    if os.getenv("DEBUG_EMAILS", "false").lower() == "true":
        print(f"Email to {to_email}\nSubject: {subject}\n{body}")
        return

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = os.getenv("EMAIL_FROM")
    msg["To"] = to_email

    try:
        with smtplib.SMTP(os.getenv("SMTP_SERVER"), int(os.getenv("SMTP_PORT"))) as server:
            server.starttls()
            server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
            server.send_message(msg)
            print(f"Email sent successfully to {to_email}")
    except Exception as e:
        print(f"Error sending email: {e}")
