#!/usr/bin/env python
"""
This is a Python script that automates
* Checks if cached credentials exists in .aws/cli/cache
* If exists, checks if credentials are expired
* If expired, updates cached credentials in .aws/cli/cache by running `export BROWSER='/bin/echo';aws sso login`
    1. Navigates to the one-time-link given by the above cmd through selenium in a headless chrome browser
    2. Waits for redirect to OKTA login page
    3. Enters username and password and clicks enter
    4. On successful login, clicks on 'Login to cli'
    5. Exits headless browser
    6. Waits for shell cmd to exit with message 'Successfully logged into '
* Writes cached credentials to .aws/credentails
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from progress.bar import Bar
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import visibility_of_element_located, element_to_be_clickable
from selenium.webdriver.support.wait import WebDriverWait

from commandwatch import CommandWatch

start_pattern = "https://device\.sso\.[a-z0-9-]+\.amazonaws\.com/\?user_code=[a-zA-Z0-9]+"
end_pattern = "Successully logged into Start URL: https://.+\.awsapps\.com/start"


def aws_login_sso(args):
    bar = Bar('Injecting AWS credentials', max=21)
    bar.next(1)
    files = sorted(Path(os.path.expanduser("~/.aws/cli/cache")).iterdir(), key=os.path.getmtime)
    profile = args.profile
    username = args.username
    if not username:
        username = os.environ.get('AWS_SSO_USERNAME')
    password = args.password
    if not password:
        password = os.environ.get('AWS_SSO_PASSWORD')
    credentials_file = args.credentials_file
    if not credentials_file:
        credentials_file = os.environ.get('AWS_CRED_FILE')
        if not credentials_file:
            credentials_file = "~/.aws/credentials"
    run_aws_sso_login = False
    if len(files) == 0:
        run_aws_sso_login = True
    else:
        with open(files[0], 'r') as creds:
            readFile = creds.read()
            cached_creds = json.loads(readFile)
            if 'Credentials' in cached_creds:
                credentials = cached_creds.get('Credentials')
                if 'Expiration' in credentials:
                    expires = datetime.strptime(credentials.get('Expiration'), "%Y-%m-%dT%H:%M:%SZ")
                    if expires < datetime.now():
                        run_aws_sso_login = True
    if run_aws_sso_login:
        aws_login_watch = CommandWatch(cmd="export BROWSER='/bin/echo';aws sso login", countdown=1,
                                       match_pattern=start_pattern, end_pattern=end_pattern)
        aws_login_watch.submit(200)
        time.sleep(2)
        while not len(aws_login_watch.matched_lines) > 0:
            time.sleep(1)
        bar.next(2)
        url = aws_login_watch.matched_lines[0].rstrip()
        if not username and not password:
            sys.exit(
                'Usage: Required params AWS_SSO_USERNAME, and AWS_SSO_PASSWORD not passed and not found in '
                'environment. To set as environment variables, execute `export AWS_SSO_USERNAME=XYZ; export AWS_SSO_PASSWORD=ABC`')
        bar.next()
        options = Options()
        options.headless = True
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        bar.next()
        WebDriverWait(driver, 100).until(visibility_of_element_located((By.ID, 'okta-signin-username')))
        bar.next()
        driver.find_element_by_id('okta-signin-username').send_keys(username)
        driver.find_element_by_id('okta-signin-password').send_keys(password)
        driver.find_element_by_id('okta-signin-submit').click()
        bar.next()
        WebDriverWait(driver, 100).until(element_to_be_clickable(
            (By.XPATH, "//*[@id='cli_login_button']"))).click()
        bar.next()
        element = WebDriverWait(driver, 100).until(element_to_be_clickable((By.XPATH,
                                                                            "//*[@id='containerFrame']/div/div/div/div/div/h4/p[2]")))
        if not element.text == 'You can now close this browser.':
            driver.close()
            sys.exit('Error: Unable to complete CLI form submission')
        driver.close()
        time.sleep(5)
        bar.next(3)
    else:
        bar.next(10)
    files = sorted(Path(os.path.expanduser("~/.aws/cli/cache")).iterdir(), key=os.path.getmtime)
    if len(files) > 0:
        with open(files[0], 'r') as creds:
            bar.next()
            readFile = creds.read()
            cached_creds = json.loads(readFile)
            # AWS_ACCESS_KEY_ID
            aws_access_key_id = cached_creds['Credentials'].get('AccessKeyId')
            # AWS_SECRET_ACCESS_KEY
            aws_secret_access_key = cached_creds['Credentials'].get('SecretAccessKey')
            # AWS_SESSION_TOKEN
            aws_secret_session_token = cached_creds['Credentials'].get('SessionToken')
            file = os.path.expanduser(credentials_file)
            bar.next()
            if not os.path.exists(file):
                with open(file, 'w') as f:
                    bar.next()
                    f.write(f'[{profile}]' + "\n")
                    write_aws_creds(aws_access_key_id, aws_secret_access_key, aws_secret_session_token, f)
                    bar.next()
            else:
                in_profile = False
                with open(file, 'r+') as f:
                    lines = f.readlines()  # read everything in the file
                    f.seek(0)
                    i = 0
                    bar.next()
                    while i < len(lines):
                        bar.next()
                        line = lines[i]
                        if line in ['\n', '\r\n']:
                            in_profile = False
                        elif line.startswith('['):
                            value_profile = line.split('[')[1].split(']')[0]
                            if value_profile == profile:
                                in_profile = True
                                f.write(line)
                                write_aws_creds(aws_access_key_id, aws_secret_access_key, aws_secret_session_token, f)
                                i += 1
                                continue
                            else:
                                in_profile = False
                        elif (line.startswith('aws_access_key_id=') or \
                              line.startswith('aws_secret_access_key=') or \
                              line.startswith('aws_session_token=')) and in_profile:
                            i += 1
                            continue
                        f.write(line)
                        i += 1
                    bar.next(3)
    bar.finish()


def write_aws_creds(aws_access_key_id, aws_secret_access_key, aws_secret_session_token, f):
    f.write(f'aws_access_key_id="{aws_access_key_id}"' + "\n")
    f.write(f'aws_secret_access_key="{aws_secret_access_key}"' + "\n")
    f.write(f'aws_session_token="{aws_secret_session_token}"' + "\n")


# Main method
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get cmd line variables')
    parser.add_argument('--profile', '-o', default='default', required=False, dest='profile',
                        help='Destination profile')
    parser.add_argument('--url', '-l', required=False, dest='url', help='AWS_SSO_URL')
    parser.add_argument('--username', '-u', required=False, dest='username', help='AWS_SSO_USERNAME')
    parser.add_argument('--password', '-p', required=False, dest='password', help='AWS_SSO_PASSWORD')
    parser.add_argument('--aws-cred-file', '-f', required=False, dest='credentials_file', help='AWS_CRED_FILE')
    args = parser.parse_args()
    aws_login_sso(args)
