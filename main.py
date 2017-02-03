#!/usr/bin/env python3
import re
import requests
import smtplib
from email.mime.text import MIMEText
from email import utils
import logging

logging.basicConfig(filename='error.log', level=logging.INFO)

CHANGELOG = ''
# Mail
HOST = ''
PORT = ''
USER = ''
PASSWORD = ''
TARGET = ''


def getLocalVersion():
    pattern = re.compile("Server Release (\d+.\d+.\d+.\d+)")
    with open(CHANGELOG, 'r') as f:
        versions = re.findall(pattern, str(f.read()))
        return str(versions[0])


def getCurrentVersion():
    r = requests.get("https://www.teamspeak.com/versions/server.json")
    json = r.json()
    return str(json['linux']['x86_64']['version'])  # you might want to modify this


def sendMail(message):
    msg = MIMEText(message)
    msg['Subject'] = 'TS3 version'
    msg['From'] = USER
    msg['To'] = TARGET
    msg['Date'] = utils.formatdate(localtime=True)

    server = smtplib.SMTP(host=HOST, port=PORT)
    # server.set_debuglevel(1)
    server.starttls()
    server.ehlo()
    server.login(user=USER, password=PASSWORD)
    server.sendmail(from_addr=USER, to_addrs=TARGET,
                    msg=msg.as_string())


def main():
    message = ""
    try:
        local = getLocalVersion()
        current = getCurrentVersion()
    except OSError as e:
        message = "An error occurred while trying to read the local CHANGELOG file: %s" % e
    except requests.RequestException as e:
        message.join("An error occurred while trying to get the current version: %s" % e)
    if message == "":
        if local != current:
            message = "There is a new ts3 server version: %s, your version: %s" % (current, local)
            try:
                sendMail(message)
            except smtplib.SMTPException as e:
                logging.error("Could not send an email: %s" % e)
        else:
            logging.info("Same version, no mail")

    else:
        try:
            sendMail(message)
        except smtplib.SMTPException as e:
            logging.error("Could not send an email: %s" % e)


if __name__ == '__main__':
    main()
