# Actual sending function
import smtplib

# Email modules
from email.mime.text import MIMEText

# Send a message of some text document with some subject
def send_message(text_doc, subject="Notification",
                 sender="notice", reciever="supervisor"):
    with open(text_doc) as tx:
        msg = MIMEText(tx.read())

    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = reciever

    # TODO: Setup email server on ornl host.
    s = smtplib.SMTP('localhost')
    s.send_message(msg)
    s.quit()
