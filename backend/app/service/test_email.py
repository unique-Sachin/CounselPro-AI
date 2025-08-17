import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()


async def test_gmail():
    # Gmail credentials
    sender = os.getenv("EMAIL_USERNAME")
    password = os.getenv("EMAIL_PASSWORD")
    recipient = "ravinjangir.rj1100@gmail.com"

    # Create message
    message = MIMEMultipart()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = "Test Email from CounselPro"

    body = """
    <html>
        <body>
            <h1>Test Email</h1>
            <p>This is a test email from CounselPro AI.</p>
        </body>
    </html>
    """
    message.attach(MIMEText(body, "html"))

    # Connect to Gmail
    async with aiosmtplib.SMTP(
        hostname="smtp.gmail.com", port=465, use_tls=True
    ) as smtp:
        print("Connecting to Gmail...")
        await smtp.login(sender, password)
        print("Logged in successfully")
        await smtp.send_message(message)
        print("Email sent successfully!")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_gmail())
