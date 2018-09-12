# Actual sending function
import smtplib

# Email modules
from email.message import EmailMessage
import os

# Send a message of some text document with some subject
def send_message(text_doc, subject, sender, reciever):

    with open(text_doc) as tx:
        msg = EmailMessage()
        msg.set_content(tx.read())

    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = reciever

    s = smtplib.SMTP('localhost')
    print('Host found.')
    s.send_message(msg)
    print('Message sent.')
    s.quit()

if __name__ == "__main__":
    email_path = os.path.dirname(__file__) + "/test_email.txt"
    send_message(text_doc=email_path, subject='Notification', sender='OLCF-notice', reciever='human_being')

