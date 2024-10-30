import os
import ssl
import smtplib

from fastapi import HTTPException
# from .google_api.Google import Create_Service
# import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
load_dotenv()
API_NAME = 'gmail'
API_VERSION = 'v1'
SCOPES = ['https://mail.google.com/']


class EmailSender:
    def __init__(self):
        self.email_sender = os.environ.get("EMAIL_SENDER")
        self.email_password = os.environ.get("EMAIL_PASSWORD")
        self.smtp_server = os.environ.get("SMTP_SERVER")
        self.port = 465
        self.context = ssl.create_default_context()
        # ตรวจสอบว่าตัวแปรทั้งหมดถูกตั้งค่าหรือไม่
        if not all([self.email_sender, self.email_password, self.smtp_server]):
            raise ValueError("Environment variables for email are not fully set.")

    def sendEmail(self, receiver_email: str, token: str):
        emailMsg = f"""
                    <!DOCTYPE html>
                    <html lang="en">
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>Password Reset</title>
                        <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
                    </head>
                    <body>
                        <div class="container">
                            <div class="row justify-content-center">
                                <div class="col-md-8">
                                    <div class="card mt-5">
                                        <div class="card-header">
                                            <h2 class="text-center">Reset Password</h2>
                                        </div>
                                        <div class="card-body">
                                            <p class="lead">
                                                A password reset request has been initiated for your account.
                                            </p>
                                            <a  class="btn btn-primary" href="http://localhost:4200/reset-password?reset_token={token}">Reset password Link</a>
                                        
                                            <p class="lead">
                                                Please note that this token is valid for a limited time.
                                                If you did not request a password reset, you can safely disregard this email.
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </body>
                    </html>
                    """
        em = MIMEMultipart()
        em['From'] = self.email_sender
        em['To'] = receiver_email
        em['Subject'] = "Link Reset Password Request"
        em.attach(MIMEText(emailMsg, 'html'))
        try:
            with smtplib.SMTP_SSL(self.smtp_server,self.port,context=self.context) as smtp:
                smtp.login(self.email_sender, self.email_password)
                smtp.sendmail(self.email_sender, receiver_email, em.as_string())
            print("HTML email sent successfully!")
        except Exception as e:
                raise HTTPException(status_code=500, detail=f"Server Interval Error: {e.message}")




# def sendEmail(receiver_email: str, token: str):
#     service = Create_Service(API_NAME, API_VERSION, SCOPES)

#     # Customize email message
#     emailMsg = f"""
#     <!DOCTYPE html>
#     <html lang="en">
#     <head>
#         <meta charset="UTF-8">
#         <meta name="viewport" content="width=device-width, initial-scale=1.0">
#         <title>Password Reset</title>
#         <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
#     </head>
#     <body>
#         <div class="container">
#             <div class="row justify-content-center">
#                 <div class="col-md-8">
#                     <div class="card mt-5">
#                         <div class="card-header">
#                             <h2 class="text-center">Reset Password</h2>
#                         </div>
#                         <div class="card-body">
#                             <p class="lead">
#                                 A password reset request has been initiated for your account.
#                             </p>
#                             <a  class="btn btn-primary" href="http://localhost:4200/reset-password?reset_token={token}">Reset password Link</a>
                           
#                             <p class="lead">
#                                 Please note that this token is valid for a limited time.
#                                 If you did not request a password reset, you can safely disregard this email.
#                             </p>
#                         </div>
#                     </div>
#                 </div>
#             </div>
#         </div>
#     </body>
#     </html>
#     """
#     # Create MIME message
#     mimeMessage = MIMEMultipart()
#     mimeMessage['to'] = receiver_email
#     mimeMessage['subject'] = 'Reset Password Request'

#     # Attach HTML email body
#     mimeMessage.attach(MIMEText(emailMsg, 'html'))

#     # Encode message to raw string
#     raw_string = base64.urlsafe_b64encode(mimeMessage.as_bytes()).decode()

#     # Send email
#     message = service.users().messages().send(
#         userId='me', body={'raw': raw_string}).execute()
#     print(message)
