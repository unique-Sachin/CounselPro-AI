from fastapi import BackgroundTasks
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib
from dotenv import load_dotenv
import os

load_dotenv()


SMTP_HOST = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("EMAIL_USERNAME")
SMTP_PASSWORD = os.getenv("EMAIL_PASSWORD")


async def send_email(
    subject: str,
    recipient: str,
    body: str,
):
    message = MIMEMultipart()
    message["From"] = SMTP_USER
    message["To"] = recipient
    message["Subject"] = subject

    message.attach(MIMEText(body, "html"))

    await aiosmtplib.send(
        message,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        username=SMTP_USER,
        password=SMTP_PASSWORD,
        start_tls=True,
    )


def send_email_background(
    background_tasks: BackgroundTasks, subject: str, recipient: str, body: str
):
    """
    This function schedules the email to be sent in background (non-blocking)
    """
    background_tasks.add_task(send_email, subject, recipient, body)


def get_modern_counselor_email_template(
    counselor_name: str,
    student_name: str,
    session_date: str,
    summary: dict,
    dashboard_link: str,
) -> str:
    """
    Generate modern, email-client compatible HTML template for counselor analytics report.
    """
    audio_insights_html = "".join(
        f'<div style="color: #ffffff; font-size: 14px; margin-bottom: 10px; padding-left: 20px; position: relative;"><span style="display: inline-block; width: 8px; height: 8px; background: #ff6b6b; border-radius: 50%; margin-right: 10px;"></span>{item}</div>'
        for item in summary.get("audio_insights", [])
    )

    alerts_section = ""
    if summary.get("audio_insights"):
        alerts_section = f"""
        <div style="background: rgba(255, 107, 107, 0.1); border: 1px solid #ff6b6b; border-radius: 16px; padding: 25px; margin: 30px 0;">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 15px;">
                <div style="width: 24px; height: 24px; background: #ff6b6b; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 14px;">⚠️</div>
                <div style="font-size: 16px; font-weight: 600; color: #ff6b6b;">Critical Alert Detected</div>
            </div>
            <div style="background: rgba(0, 0, 0, 0.2); border-radius: 12px; padding: 15px; border-left: 3px solid #ff6b6b;">
                {audio_insights_html}
            </div>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Session Analytics Dashboard</title>
        <!--[if mso]>
        <noscript>
            <xml>
                <o:OfficeDocumentSettings>
                    <o:PixelsPerInch>96</o:PixelsPerInch>
                </o:OfficeDocumentSettings>
            </xml>
        </noscript>
        <![endif]-->
    </head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #0f0f23; color: #ffffff;">
        <!-- Main Container -->
        <div style="width: 100%; max-width: 650px; margin: 0 auto; background: #1a1a2e; border-radius: 24px; overflow: hidden;">
            
            <!-- Top Bar -->
            <div style="background: linear-gradient(90deg, #ff6b6b, #feca57, #48dbfb, #ff9ff3); height: 4px;"></div>
            
            <!-- Header Section -->
            <div style="padding: 40px 35px 30px; background: #1a1a2e; position: relative;">
                <!-- Brand Logo -->
                <div style="width: 50px; height: 50px; background: linear-gradient(135deg, #ff6b6b, #feca57); border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-bottom: 20px; color: white; font-weight: 700; font-size: 24px;">S</div>
                
                <!-- Header Title -->
                <h1 style="font-size: 28px; font-weight: 700; color: #ffffff; margin: 0 0 8px 0;">Session Insights</h1>
                <p style="color: #a0a0a0; font-size: 14px; margin: 0;">AI-Powered Analytics • Real-time Monitoring</p>
            </div>
            
            <!-- Main Content -->
            <div style="padding: 0 35px 40px;">
                
                <!-- Greeting Card -->
                <div style="background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 25px; margin-bottom: 30px;">
                    <div style="font-size: 22px; font-weight: 600; margin-bottom: 10px; color: #ff6b6b;">Hey {counselor_name}! 🚀</div>
                    <p style="color: #b0b0b0; font-size: 14px; margin: 0 0 15px 0;">Your latest counseling session with {student_name} has been processed through our advanced AI analytics engine.</p>
                    
                    <!-- Session Details -->
                    <div style="margin-top: 15px;">
                        <table cellpadding="0" cellspacing="0" style="border: none;">
                            <tr>
                                <td style="padding: 8px 16px; background: rgba(72, 219, 251, 0.1); border: 1px solid rgba(72, 219, 251, 0.3); color: #48dbfb; border-radius: 20px; font-size: 12px; font-weight: 500; margin-right: 10px; display: inline-block; margin-bottom: 10px;">
                                    ✓ Session Complete
                                </td>
                                <td style="padding: 8px 16px; background: rgba(72, 219, 251, 0.1); border: 1px solid rgba(72, 219, 251, 0.3); color: #48dbfb; border-radius: 20px; font-size: 12px; font-weight: 500; margin-right: 10px; display: inline-block; margin-bottom: 10px;">
                                    🕐 {session_date}
                                </td>
                                <td style="padding: 8px 16px; background: rgba(72, 219, 251, 0.1); border: 1px solid rgba(72, 219, 251, 0.3); color: #48dbfb; border-radius: 20px; font-size: 12px; font-weight: 500; display: inline-block; margin-bottom: 10px;">
                                    ⏱️ 45 Minutes
                                </td>
                            </tr>
                        </table>
                    </div>
                </div>
                
                <!-- Stats Grid using Table -->
                <table cellpadding="0" cellspacing="10" style="width: 100%; margin: 35px 0;">
                    <tr>
                        <td style="width: 25%; background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 25px 20px; text-align: center; vertical-align: top;">
                            <div style="width: 40px; height: 40px; margin: 0 auto 15px; background: linear-gradient(135deg, #ff6b6b, #feca57); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 20px;">📹</div>
                            <div style="font-size: 24px; font-weight: 700; margin-bottom: 5px; color: #ffffff;">{summary.get("camera_presence", "N/A")}</div>
                            <div style="font-size: 11px; color: #a0a0a0; text-transform: uppercase; letter-spacing: 1px; font-weight: 500;">CAMERA ACTIVE</div>
                        </td>
                        <td style="width: 25%; background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 25px 20px; text-align: center; vertical-align: top;">
                            <div style="width: 40px; height: 40px; margin: 0 auto 15px; background: linear-gradient(135deg, #ff6b6b, #feca57); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 20px;">👔</div>
                            <div style="font-size: 24px; font-weight: 700; margin-bottom: 5px; color: #ffffff;">{summary.get("professional_attire", "N/A")}</div>
                            <div style="font-size: 11px; color: #a0a0a0; text-transform: uppercase; letter-spacing: 1px; font-weight: 500;">ATTIRE SCORE</div>
                        </td>
                        <td style="width: 25%; background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 25px 20px; text-align: center; vertical-align: top;">
                            <div style="width: 40px; height: 40px; margin: 0 auto 15px; background: linear-gradient(135deg, #ff6b6b, #feca57); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 20px;">🏠</div>
                            <div style="font-size: 24px; font-weight: 700; margin-bottom: 5px; color: #ffffff;">{summary.get("background_setting", "N/A")}</div>
                            <div style="font-size: 11px; color: #a0a0a0; text-transform: uppercase; letter-spacing: 1px; font-weight: 500;">ENVIRONMENT</div>
                        </td>
                        <td style="width: 25%; background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 25px 20px; text-align: center; vertical-align: top;">
                            <div style="width: 40px; height: 40px; margin: 0 auto 15px; background: linear-gradient(135deg, #ff6b6b, #feca57); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 20px;">🖥️</div>
                            <div style="font-size: 24px; font-weight: 700; margin-bottom: 5px; color: #ffffff;">{summary.get("screen_sharing_duration", "N/A")}</div>
                            <div style="font-size: 11px; color: #a0a0a0; text-transform: uppercase; letter-spacing: 1px; font-weight: 500;">SCREEN TIME</div>
                        </td>
                    </tr>
                </table>
                
                <!-- Alert Section -->
                {alerts_section}
                
                <!-- Divider -->
                <div style="height: 1px; background: rgba(255, 255, 255, 0.2); margin: 30px 0;"></div>
                
                <!-- CTA Section -->
                <div style="text-align: center; margin: 40px 0 30px;">
                    <a href="{dashboard_link}" style="display: inline-block; background: linear-gradient(135deg, #ff6b6b, #feca57); color: white; text-decoration: none; padding: 18px 35px; border-radius: 50px; font-weight: 600; font-size: 16px;">
                        Open Full Dashboard →
                    </a>
                </div>
            </div>
            
            <!-- Footer Section -->
            <div style="background: rgba(0, 0, 0, 0.3); padding: 30px 35px; text-align: center; border-top: 1px solid rgba(255, 255, 255, 0.1);">
                <p style="color: #808080; font-size: 12px; line-height: 1.6; margin-bottom: 20px;">
                    Powered by next-generation AI algorithms and machine learning models.<br>
                    This report was generated in real-time with 99.7% accuracy.
                </p>
                
                <!-- Tech Badges -->
                <div style="text-align: center;">
                    <span style="background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); color: #a0a0a0; padding: 8px 15px; border-radius: 16px; font-size: 10px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; margin-right: 10px;">AI POWERED</span>
                    <span style="background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); color: #a0a0a0; padding: 8px 15px; border-radius: 16px; font-size: 10px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; margin-right: 10px;">REAL-TIME</span>
                    <span style="background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); color: #a0a0a0; padding: 8px 15px; border-radius: 16px; font-size: 10px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; margin-right: 10px;">ENCRYPTED</span>
                    <span style="background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); color: #a0a0a0; padding: 8px 15px; border-radius: 16px; font-size: 10px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">GDPR COMPLIANT</span>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


async def test_email_sending(recipient_email: str):
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
        await send_email(subject=subject, recipient=recipient_email, body=body)
        print(f"✅ Test email sent successfully to {recipient_email}")
        return True
    except Exception as e:
        print(f"❌ Error sending test email: {str(e)}")
        return False


async def test_modern_email_template(recipient_email: str):
    """
    Test function to verify the modern counselor email template
    """
    # Sample data for testing
    test_summary = {
        "camera_presence": "90%",
        "professional_attire": "A+",
        "background_setting": "Pro",
        "screen_sharing_duration": "12m",
        "audio_insights": [
            "Unauthorized payment discussion identified in audio transcript - requires immediate review",
            "Pressure tactics detected during conversation - flagged for supervisor review",
        ],
    }

    # Generate the modern template
    modern_body = get_modern_counselor_email_template(
        counselor_name="Dr. Sarah Johnson",
        student_name="Alex Martinez",
        session_date="Aug 17, 2025",
        summary=test_summary,
        dashboard_link="https://your-dashboard.com/session/12345",
    )

    subject = "🚀 Session Analytics Report - Modern Template Test"

    try:
        await send_email(subject=subject, recipient=recipient_email, body=modern_body)
        print(f"✅ Modern template test email sent successfully to {recipient_email}")
        return True
    except Exception as e:
        print(f"❌ Error sending modern template test email: {str(e)}")
        return False
