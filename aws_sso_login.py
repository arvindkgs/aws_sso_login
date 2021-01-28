#!/usr/bin/env python
'''
This is a Python script that automates injecting aws session env into current shell by automating below steps:
1. Gets AWS_SSO_URL, which redirects to OKTA login page
2. Enters username and password and clicks enter
3. On successful login, clicks on user account icon on aws sso page
4. Captures session token, secret id
5. Writes to AWS_CRED_FILE
6. Also outputs export commands (that can used to set as env variables):
 * export AWS_ACCESS_KEY_ID=123; export AWS_SECRET_ACCESS_KEY=123; export AWS_SESSION_TOKEN=123
'''
import argparse
import os
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import visibility_of_element_located, element_to_be_clickable, \
    presence_of_element_located
from selenium.webdriver.support.wait import WebDriverWait


def aws_login_sso(args):
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
    url = args.url
    if not url:
        url = os.environ.get('AWS_SSO_URL')
    if not username and not password and not url:
        sys.exit(
            'Usage: Required params AWS_SSO_USERNAME, AWS_SSO_PASSWORD and AWS_SSO_URL not passed and not found in '
            'environment. To set as environment variables, execute `export USERNAME=XYZ; export PASSWORD=ABC`')
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    WebDriverWait(driver, 100).until(visibility_of_element_located((By.ID, 'okta-signin-username')))
    driver.find_element_by_id('okta-signin-username').send_keys(username)
    driver.find_element_by_id('okta-signin-password').send_keys(password)
    driver.find_element_by_id('okta-signin-submit').click()
    WebDriverWait(driver, 100).until(element_to_be_clickable(
        (By.XPATH, "/html/body/app/portal-ui/div/portal-dashboard/portal-application-list/portal-application"))).click()
    WebDriverWait(driver, 100).until(element_to_be_clickable((By.XPATH,
                                                              "/html/body/app/portal-ui/div/portal-dashboard/portal"
                                                              "-application-list/sso-expander/portal-instance-list"
                                                              "/div[1]/portal-instance/div/div"))).click()
    WebDriverWait(driver, 100).until(element_to_be_clickable((By.XPATH,
                                                              "/html/body/app/portal-ui/div/portal-dashboard/portal"
                                                              "-application-list/sso-expander/portal-instance-list/"
                                                              "div[1]/portal-instance/div/sso-expander/portal-profile-list"
                                                              "/div/portal-profile/span/span/span[2]/a"))).click()
    WebDriverWait(driver, 100).until(presence_of_element_located((By.XPATH,
                                                                  "/html/body/app/portal-ui/div/portal-dashboard/portal-application-list/sso-expander/portal-instance-list/div[1]/portal-instance/div/sso-expander/portal-profile-list/div/portal-profile/span/span/span[2]/creds-modal/sso-modal/div/div/div[1]/h2")))
    WebDriverWait(driver, 100).until(presence_of_element_located((By.XPATH,
                                                                  "//*[@class='code-line ng-tns-c19-8']")))
    time.sleep(2)
    elements = driver.find_elements_by_xpath("//*[@class='code-line ng-tns-c19-8']")
    # AWS_ACCESS_KEY_ID
    cmd_aws_access_key_id = elements[0].get_attribute('innerText')
    print(cmd_aws_access_key_id + ";")
    aws_access_key_id = cmd_aws_access_key_id.split('"')[1]
    # AWS_SECRET_ACCESS_KEY
    cmd_aws_secret_access_key = elements[1].get_attribute('innerText')
    print(cmd_aws_secret_access_key + ";")
    aws_secret_access_key = cmd_aws_secret_access_key.split('"')[1]
    # AWS_SESSION_TOKEN
    cmd_aws_session_token = elements[2].get_attribute('innerText')
    print(cmd_aws_session_token + ";")
    aws_secret_session_token = cmd_aws_session_token.split('"')[1]
    file = os.path.expanduser(credentials_file)
    if not os.path.exists(file):
        with open(file, 'w') as f:
            f.write(f'[{profile}]' + "\n")
            write_aws_creds(aws_access_key_id, aws_secret_access_key, aws_secret_session_token, f)
    else:
        in_profile = False
        with open(file, 'r+') as f:
            lines = f.readlines()  # read everything in the file
            f.seek(0)
            i = 0
            while i < len(lines):
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
