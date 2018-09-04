# Actual sending function
import smtplib

# Email modules
from email.message import EmailMessage

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
    send_message(text_doc='./test_email.txt', subject='Notification', sender='OLCF-notice', reciever='kuchtact@beloit.edu')

