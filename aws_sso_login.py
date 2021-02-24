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
import logging
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import visibility_of_element_located, element_to_be_clickable
from selenium.webdriver.support.wait import WebDriverWait

from commandwatch import CommandWatch

start_pattern = "https://device\.sso\.[a-z0-9-]+\.amazonaws\.com/\?user_code=[a-zA-Z0-9-]+"
end_pattern = "Successully logged into Start URL: https://.+\.awsapps\.com/start"


def aws_login_sso(args):
    logger = logging.getLogger("aws_login_sso")
    logger.setLevel(logging.INFO)
    h1 = logging.FileHandler(filename="sso_login.log")
    h1.setLevel(logging.INFO)
    logger.addHandler(h1)
    # bar = Bar('Injecting AWS credentials', max=22)
    # bar.next(1)
    files = sorted(Path(os.path.expanduser("~/.aws/cli/cache")).iterdir(), key=os.path.getmtime)
    username = args.username
    if not username:
        logger.info("Using 'AWS_SSO_USERNAME' from env")
        username = os.environ.get('AWS_SSO_USERNAME')
    password = args.password
    if not password:
        logger.info("Using 'AWS_SSO_PASSWORD' from env")
        password = os.environ.get('AWS_SSO_PASSWORD')
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
                        logger.info(f'{creds.name} expired!')
                        run_aws_sso_login = True
    if run_aws_sso_login:
        logger.info('Logging in to SSO')
        aws_login_watch = CommandWatch(cmd="export BROWSER='/bin/echo';aws2 sso login", countdown=1,
                                       end_pattern=end_pattern, match_pattern=start_pattern)
        aws_login_watch.submit(200)
        time.sleep(2)
        while not len(aws_login_watch.matched_lines) > 0:
            time.sleep(1)
        #bar.next(2)
        url = aws_login_watch.matched_lines[0].rstrip()
        if not username and not password:
            sys.exit(
                'Usage: Required params AWS_SSO_USERNAME, and AWS_SSO_PASSWORD not passed and not found in '
                'environment. To set as environment variables, execute `export AWS_SSO_USERNAME=XYZ; export AWS_SSO_PASSWORD=ABC`')
        #bar.next()
        options = Options()
        #options.headless = True
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        #bar.next()
        WebDriverWait(driver, 100).until(visibility_of_element_located((By.ID, 'okta-signin-username')))
        #bar.next()
        driver.find_element_by_id('okta-signin-username').send_keys(username)
        driver.find_element_by_id('okta-signin-password').send_keys(password)
        driver.find_element_by_id('okta-signin-submit').click()
        #bar.next()
        WebDriverWait(driver, 100).until(element_to_be_clickable(
            (By.XPATH, "//*[@id='cli_login_button']"))).click()
        #bar.next()
        element = WebDriverWait(driver, 100).until(element_to_be_clickable((By.XPATH,
                                                                            "//*[@id='containerFrame']/div/div/div/div/div/h4/p[2]")))
        if not element.text == 'You can now close this browser.':
            driver.close()
            sys.exit('Error: Unable to complete CLI form submission')
        driver.close()
        time.sleep(3)
        #bar.next(3)
    else:
        #bar.next(7)
        logger.info('Skipping SSO!')
        pass


def write_aws_creds(aws_access_key_id, aws_secret_access_key, aws_secret_session_token, f):
    f.write(f'aws_access_key_id="{aws_access_key_id}"' + "\n")
    f.write(f'aws_secret_access_key="{aws_secret_access_key}"' + "\n")
    f.write(f'aws_session_token="{aws_secret_session_token}"' + "\n")


# Main method
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get cmd line variables')
    parser.add_argument('--username', '-u', required=False, dest='username', help='AWS_SSO_USERNAME')
    parser.add_argument('--password', '-p', required=False, dest='password', help='AWS_SSO_PASSWORD')
    args = parser.parse_args()
    aws_login_sso(args)
