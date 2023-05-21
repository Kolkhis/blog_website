import smtplib
import os
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText

BOT_EMAIL = os.environ['BOT_EMAIL']
APP_PASSWORD = os.environ['EMAIL_PASSWORD']


class EmailManager:
    def __init__(self):
        # self.message = MIMEMultipart()
        self.msg_text = ''

    def create_email(self, data: dict):
        """Formats the email as a MIMEMultipart message."""
        self.msg_text = f"From:{data['email']}\n" \
                        f"To: {BOT_EMAIL}\n" \
                        f"Subject: Message from {data['name']}, from the blog site.\n\n" \
                        f"{data['message']}"
        # self.message.add_header('subject', f'message from {data["name"]}, a reader!')
        # self.message.add_header('from', data['email'])
        # self.message.add_header('to', BOT_EMAIL)
        # msg_body = MIMEText(_text=f'message from {data["name"]}:\n'
        #                           f'{data["message"]}\n\n' \
        #                           f'phone number: {data["phone"]}\n'
        #                           f'email addr:   {data["email"]}')
        # self.message.attach(msg_body)

    def send_email(self, data: dict):
        """Creates an email from BOT_EMAIL and sends it to myself"""
        self.create_email(data)
        with smtplib.SMTP('smtp.gmail.com') as server:
            server.starttls()
            server.login(user=BOT_EMAIL, password=APP_PASSWORD)
            server.sendmail(from_addr=BOT_EMAIL, to_addrs=BOT_EMAIL, msg=self.msg_text)
