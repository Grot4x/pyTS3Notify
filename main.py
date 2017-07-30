#!/usr/bin/env python3
import re
import requests
import smtplib
import json
import sys
from email.mime.text import MIMEText
from email import utils
import logging

logging.basicConfig(filename='error.log', level=logging.INFO)

CONFIG = {}
CONFIG['CHANGELOG'] = ''
CONFIG['URL'] = 'https://www.teamspeak.com/versions/server.json'
CONFIG['MAIL'] = {}
CONFIG['MAIL']['HOST'] = ''
CONFIG['MAIL']['PORT'] = ''
CONFIG['MAIL']['USER'] = ''
CONFIG['MAIL']['PASSWORD'] = ''
CONFIG['MAIL']['TARGET'] = ''


def lastMail():
    return True


def getLocalVersion():
    pattern = re.compile("Server Release (\d+.\d+.\d+.\d+)")
    with open(CONFIG['CHANGELOG'], 'r') as f:
        versions = re.findall(pattern, str(f.read()))
        return str(versions[0])


def getCurrentVersion():
    r = requests.get(CONFIG['URL'])
    json = r.json()
    # you might want to modify this
    return str(json['linux']['x86_64']['version'])


def sendMail(message):
    msg = MIMEText(message)
    msg['Subject'] = '[TS3] Your TS3 Server needs an update'
    msg['From'] = CONFIG['MAIL']['USER']
    msg['To'] = CONFIG['MAIL']['TARGET']
    msg['Date'] = utils.formatdate(localtime=True)

    server = smtplib.SMTP(host=HOST, port=PORT)
    # server.set_debuglevel(1)
    server.starttls()
    server.ehlo()
    server.login(user=CONFIG['MAIL']['USER'],
                 password=CONFIG['MAIL']['PASSWORD'])
    server.sendmail(from_addr=CONFIG['MAIL']['USER'], to_addrs=CONFIG['MAIL']['TARGET'],
                    msg=msg.as_string())


def main():
    global CONFIG
    if len(sys.argv) > 1:
        if sys.argv[1] == "dev":
            # Developer mode
            f = open("config.json.example", 'w')
            f.write(json.dumps(CONFIG, indent=4))
            sys.exit()
    try:
        configFile = open('config.json', 'r')
        config = json.load(configFile)
        CONFIG['MAPURL'] = str(config['MAPURL'])
        CONFIG['CHANGELOG'] = str(config['CHANGELOG'])
        CONFIG['URL'] = str(config['URL'])
        CONFIG['MAIL']['HOST'] = str(config['HOST'])
        CONFIG['MAIL']['PORT'] = str(config['PORT'])
        CONFIG['MAIL']['USER'] = str(config['USER'])
        CONFIG['MAIL']['PASSWORD'] = str(config['PASSWORD'])
        CONFIG['MAIL']['TARGET'] = str(config['TARGET'])
    except ValueError as e:
        print("No config was found.")
        sys.exit()
    except KeyError as e:
        print("Setting not found: " + str(e))
        sys.exit()
    except FileNotFoundError as e:
        print("No config was found.")
        sys.exit()
        message = ""

    try:
        local = getLocalVersion()
        current = getCurrentVersion()
    except OSError as e:
        message = "An error occurred while trying to read the local CHANGELOG file: %s" % e
    except requests.RequestException as e:
        message.join(
            "An error occurred while trying to get the current version: %s" % e)

    if message == "":
        if local != current:
            if mailSend(current):
                message = "There is a new ts3 server version: %s, your version: %s" % (
                    current, local)
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
