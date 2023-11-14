import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders
import os
# def sendMail(to, fro, subject, text, files=[],server="localhost"):
def sendMail(to, fro, subject, text, server):
    assert type(to)==list
    msg = MIMEMultipart()
    msg['From'] = fro
    msg['To'] = COMMASPACE.join(to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    msg.attach( MIMEText(text) )
    smtp = smtplib.SMTP(server)
    smtp.sendmail(fro, to, msg.as_string() )
    smtp.close()

# Example:
# sendMail(['maSnun '],'phpGeek ','Hello Python!','Heya buddy! Say hello to Python! :)',['masnun.py','masnun.php'])


