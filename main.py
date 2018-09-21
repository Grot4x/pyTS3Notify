#!/usr/bin/env python3

""" Checks if a new ts3 version is available """

import re
import smtplib
import json
import sys
from email.mime.text import MIMEText
from email import utils
import requests


"""
CONFIG = {}
CONFIG['CHANGELOG'] = ''
CONFIG['URL'] = 'https://www.teamspeak.com/versions/server.json'
CONFIG['MAIL'] = {}
CONFIG['MAIL']['HOST'] = ''
CONFIG['MAIL']['PORT'] = ''
CONFIG['MAIL']['USER'] = ''
CONFIG['MAIL']['PASSWORD'] = ''
CONFIG['MAIL']['TARGET'] = ''
"""

class Ts3Notify():
    """docstring for Ts3Notify"""
    def __init__(self, config):
        super().__init__()
        self.config = config

    def get_local_version(self):
        """ parse and return the local server version """
        pattern = re.compile("Server Release (\d+.\d+.\d+.\d+)")
        versions = ""

        with open(self.config['CHANGELOG'], 'r') as changelog:
            versions = re.findall(pattern, str(changelog.read()))

        return str(versions[0])

    def get_current_version(self):
        """ load the online json and load the current version """
        result = requests.get(self.config['URL'])
        result_json = result.json()
        # you might want to modify this
        return str(result_json['linux']['x86_64']['version'])

    def send_mail(self, message):
        """ send mail according to config"""
        msg = MIMEText(message)
        msg['Subject'] = '[TS3] Your TS3 Server needs an update'
        msg['From'] = self.config['MAIL']['USER']
        msg['To'] = self.config['MAIL']['TARGET']
        msg['Date'] = utils.formatdate(localtime=True)

        server = smtplib.SMTP(host=self.config['MAIL']['HOST'], port=self.config['MAIL']['PORT'])
        # server.set_debuglevel(1)
        server.starttls()
        server.ehlo()
        server.login(user=self.config['MAIL']['USER'],
                     password=self.config['MAIL']['PASSWORD'])
        server.sendmail(from_addr=self.config['MAIL']['USER'], to_addrs=self.config['MAIL']['TARGET'],
                        msg=msg.as_string())

def main():
    """ load conifg file and create TS3 Notify object """
    config = {}
    try:
        json_config = None

        with open('config.json', 'r') as config_file:
            json_config = json.load(config_file)

        config['CHANGELOG'] = str(json_config['CHANGELOG'])
        config['URL'] = str(json_config['URL'])
        config['MAIL']['HOST'] = str(json_config['MAIL']['HOST'])
        config['MAIL']['PORT'] = str(json_config['MAIL']['PORT'])
        config['MAIL']['USER'] = str(json_config['MAIL']['USER'])
        config['MAIL']['PASSWORD'] = str(json_config['MAIL']['PASSWORD'])
        config['MAIL']['TARGET'] = str(json_config['MAIL']['TARGET'])

    except ValueError:
        print("No config was found.", file=sys.stderr)
        sys.exit()
    except KeyError as key_error:
        print("Setting not found: {}".format(key_error), file=sys.stderr)
        sys.exit()
    except FileNotFoundError:
        print("No config was found.", file=sys.stderr)
        sys.exit()
    ts3_notify = Ts3Notify(config)
    local_version = ts3_notify.get_local_version()
    current_version = ts3_notify.get_current_version()
    if current_version != local_version:
        try:
            ts3_notify.send_mail("Your Server has version: {}\n Available version is: {}\n".format(local_version, current_version))
        except smtplib.SMTPException as smtp_exception:
            print("Could not send an email: {}".format(smtp_exception), file=sys.stderr)

if __name__ == '__main__':
    main()
