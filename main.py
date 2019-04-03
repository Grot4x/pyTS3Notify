#!/usr/bin/env python3

""" Checks if a new ts3 version is available """

import re
import smtplib
import json
import sys
from email.mime.text import MIMEText
from email import utils
import argparse
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

PARSER = argparse.ArgumentParser()

PARSER.add_argument("-c", help="-c config_file")
ARGS = PARSER.parse_args()


class Ts3Notify():
    """docstring for Ts3Notify"""
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.result_json = self.load_update_data()

    def load_update_data(self, retries=0):
        """ loads json from teamspeak.com and handles errors"""
        try:
            if retries < 5:
                request = requests.get(self.config['URL'])
                request.raise_for_status()
            else:
                print("Too many retries. {}".format(retries))
                sys.exit(1)
            return request.json()
        except requests.exceptions.HTTPError as err:
            print("HTTP Error. {}".format(err))
            retries += 1
            self.load_update_data(retries)
        except requests.exceptions.Timeout:
            print("Timeout.")
            retries += 1
            self.load_update_data(retries)
        except requests.exceptions.TooManyRedirects:
            print("Too many redirects. Please check the url.")
            sys.exit(1)
        except requests.exceptions.RequestException as err:
            print("Something went wrong {}".format(err))
            sys.exit(1)
        
    def get_local_version(self):
        """ parse and return the local server version """
        pattern = re.compile("Server Release ((\d+\.)?(\d+\.)?(\*|\d+))")
        versions = ""

        with open(self.config['CHANGELOG'], 'r') as changelog:
            versions = re.findall(pattern, str(changelog.read()))

        return str(versions[0][0])

    def get_current_version(self):
        """ returns current version """
        return str(self.result_json['linux']['x86_64']['version'])
    def get_update_url(self):
        """ returns current version """
        return str(self.result_json['linux']['x86_64']['mirrors']['teamspeak.com'])
    def get_checksum(self):
        """ returns current version """
        return str(self.result_json['linux']['x86_64']['checksum'])

    def send_mail(self, message):
        """ send mail according to config"""
        msg = MIMEText(message)
        msg['Subject'] = '[TS3] Your TS3 Server needs an update'
        msg['From'] = self.config['MAIL']['USER']
        msg['To'] = self.config['MAIL']['TARGET']
        msg['Date'] = utils.formatdate(localtime=True)

        server = smtplib.SMTP(host=self.config['MAIL']['HOST'], port=self.config['MAIL']['PORT'])
        # server.set_debuglevel(1)
        server.ehlo()

        server.starttls()

        server.ehlo()

        server.login(self.config['MAIL']['USER'], self.config['MAIL']['PASSWORD'])
        server.sendmail(self.config['MAIL']['USER'], self.config['MAIL']['TARGET'], msg.as_string())

def main():
    """ load conifg file and create TS3 Notify object """
    config = {}

    try:
        json_config = None

        with open(ARGS.c, 'r') as config_file:
            json_config = json.load(config_file)

        config['CHANGELOG'] = str(json_config['CHANGELOG'])
        config['URL'] = str(json_config['URL'])
        config['MAIL'] = {}
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
    url = ts3_notify.get_update_url()
    checksum = ts3_notify.get_checksum()
    if current_version != local_version:
        try:
            ts3_notify.send_mail("Your Server has version: {}\nAvailable version is: {}\nURL: {}\nChecksum: {}".format(local_version, current_version, url, checksum))
        except smtplib.SMTPException as smtp_exception:
            print("Could not send an email: {}".format(smtp_exception), file=sys.stderr)

if __name__ == '__main__':
    main()
