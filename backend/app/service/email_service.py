from fastapi import BackgroundTasks
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# import aiosmtplib
import smtplib
from dotenv import load_dotenv
import os
from app.db.database import get_sync_db
from app.models.counselor import Counselor
from app.models.session import CounselingSession

from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException


load_dotenv()


SMTP_HOST = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("EMAIL_USERNAME")
SMTP_PASSWORD = os.getenv("EMAIL_PASSWORD")


# async def send_email(
#     subject: str,
#     recipient: str,
#     body: str,
# ):
#     message = MIMEMultipart()
#     message["From"] = SMTP_USER
#     message["To"] = recipient
#     message["Subject"] = subject

#     message.attach(MIMEText(body, "html"))

#     await aiosmtplib.send(
#         message,
#         hostname=SMTP_HOST,
#         port=SMTP_PORT,
#         username=SMTP_USER,
#         password=SMTP_PASSWORD,
#         start_tls=True,
#     )


def send_sync_email(
    subject: str,
    recipient: str,
    body: str,
):
    message = MIMEMultipart()
    message["From"] = SMTP_USER
    message["To"] = recipient
    message["Subject"] = subject

    message.attach(MIMEText(body, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(message)


def test_email_sending(recipient_email: str):
    """
    Test function to verify email sending functionality
    """
    subject = "Test Email from CounselPro AI"
    body = """
    <!DOCTYPE html>
    <html>
    <body>
        <h1>Hello World!</h1>
        <p>This is a test email from CounselPro AI system.</p>
        <p>If you received this email, the email service is working correctly.</p>
    </body>
    </html>
    """

    try:
        send_sync_email(subject=subject, recipient=recipient_email, body=body)
        print(f"✅ Test email sent successfully to {recipient_email}")
        return True
    except Exception as e:
        print(f"❌ Error sending test email: {str(e)}")
        return False


def get_simple_counselor_email_template(
    counselor_name: str,
    dashboard_link: str,
) -> str:
    """
    Generate a beautiful email template with counselor name and dashboard link
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Session Analytics</title>
    </head>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                 background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                 margin: 0; padding: 40px; min-height: 100vh;">
        
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; 
                    border-radius: 16px; overflow: hidden; 
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);">
            
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                        padding: 40px 30px; text-align: center;">
                <h1 style="margin: 0; color: white; font-size: 28px; font-weight: 300; 
                           text-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    📊 Session Analytics Ready
                </h1>
            </div>
            
            <!-- Content -->
            <div style="padding: 40px 30px;">
                <h2 style="color: #2c3e50; font-size: 24px; font-weight: 400; 
                           margin: 0 0 20px 0; line-height: 1.4;">
                    Hello {counselor_name},
                </h2>
                
                <p style="color: #5a6c7d; font-size: 16px; line-height: 1.6; 
                          margin: 0 0 25px 0;">
                    Your latest counseling session report has been processed and is now available 
                    for review. The comprehensive analytics dashboard contains valuable insights 
                    about your recent session.
                </p>
                
                <div style="text-align: center; margin: 35px 0;">
                    <a href="{dashboard_link}" 
                       style="display: inline-block; padding: 16px 32px; 
                              background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                              color: white; text-decoration: none; border-radius: 50px; 
                              font-weight: 600; font-size: 16px; text-transform: uppercase; 
                              letter-spacing: 0.5px; transition: all 0.3s ease;
                              box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);">
                        🎯 View Dashboard
                    </a>
                </div>
                
                <div style="background: #f8f9fa; border-left: 4px solid #667eea; 
                            padding: 20px; margin: 30px 0; border-radius: 0 8px 8px 0;">
                    <p style="margin: 0; color: #6c757d; font-size: 14px; line-height: 1.5;">
                        💡 <strong>Tip:</strong> Regular review of your session analytics can help 
                        improve your counseling effectiveness and track client progress over time.
                    </p>
                </div>
            </div>
            
            <!-- Footer -->
            <div style="background: #f8f9fa; padding: 25px 30px; text-align: center; 
                        border-top: 1px solid #e9ecef;">
                <p style="margin: 0; font-size: 12px; color: #6c757d; line-height: 1.4;">
                    This is an automated email from <strong>CounselPro AI</strong><br>
                    <span style="color: #adb5bd;">© 2025 CounselPro AI. All rights reserved.</span>
                </p>
            </div>
        </div>
        
        <!-- Mobile responsiveness -->
        <style>
            @media only screen and (max-width: 600px) {{
                body {{ padding: 20px !important; }}
                .container {{ margin: 0 10px !important; }}
            }}
        </style>
    </body>
    </html>
    """


def send_simple_email_template(
    db: Session,
    session_uid: str,
):
    subject = "📊 Session Analytics Report"

    try:
        # 1. Fetch session with its counselor
        query = (
            select(CounselingSession)
            .where(CounselingSession.uid == session_uid)
            .join(Counselor, CounselingSession.counselor_id == Counselor.id)
        )
        result = db.execute(query)
        session_obj = result.scalar_one_or_none()

        if not session_obj:
            print(f"❌ No session found with uid {session_uid}")
            return False

        # 2. Extract counselor info
        counselor = session_obj.counselor  # if relationship is set
        recipient_email = counselor.email
        counselor_name = counselor.name

        # 3. Build email body
        body = get_simple_counselor_email_template(
            counselor_name=counselor_name,
            dashboard_link=f"http://localhost:3000/sessions/{session_uid}",
        )

        # 4. Send email
        send_sync_email(subject=subject, recipient=recipient_email, body=body)
        print(f"✅ Email sent successfully to {recipient_email}")
        return True

    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        return False

    # 69aac6ee-03d8-4df3-aae4-5fabf59ea03e
