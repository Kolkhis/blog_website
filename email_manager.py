import smtplib
import os

BOT_EMAIL = os.environ['BOT_EMAIL']
APP_PASSWORD = os.environ['EMAIL_PASSWORD']


class EmailManager:
    def __init__(self):
        self.msg_text = ''

    def create_email(self, data: dict):
        """Formats the email as a message."""
        self.msg_text = f"From:{data['email']}\n" \
                        f"To: {BOT_EMAIL}\n" \
                        f"Subject: Message from {data['name']}, from the blog site.\n\n" \
                        f"Registered Email:{data['registered_email']}" \
                        f"Phome number: {data['phone']}" \
                        f"{data['message']}"

    def send_email(self, data: dict):
        """Creates an email from BOT_EMAIL and sends it to itself"""
        self.create_email(data)
        with smtplib.SMTP('smtp.gmail.com') as server:
            server.starttls()
            server.login(user=BOT_EMAIL, password=APP_PASSWORD)
            server.sendmail(from_addr=BOT_EMAIL, to_addrs=BOT_EMAIL, msg=self.msg_text)
