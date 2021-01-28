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
import os
import sys
import time
import progressbar
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import visibility_of_element_located, element_to_be_clickable, \
    presence_of_element_located
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
import argparse


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
    if not username and not password:
        sys.exit(
            'Usage: Required params USERNAME and PASSWORD not passed and not found in environment. To set as '
            'environment variables, execute `export USERNAME=XYZ; export PASSWORD=ABC`')
    bar = progressbar.ProgressBar(maxval=15, \
                                  widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage()])
    bar.start()
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    bar.update(1)
    WebDriverWait(driver, 100).until(visibility_of_element_located((By.ID, 'okta-signin-username')))
    bar.update(2)
    driver.find_element_by_id('okta-signin-username').send_keys(username)
    driver.find_element_by_id('okta-signin-password').send_keys(password)
    driver.find_element_by_id('okta-signin-submit').click()
    bar.update(3)
    WebDriverWait(driver, 100).until(element_to_be_clickable(
        (By.XPATH, "/html/body/app/portal-ui/div/portal-dashboard/portal-application-list/portal-application"))).click()
    bar.update(4)
    WebDriverWait(driver, 100).until(element_to_be_clickable((By.XPATH,
                                                              "/html/body/app/portal-ui/div/portal-dashboard/portal"
                                                              "-application-list/sso-expander/portal-instance-list"
                                                              "/div[1]/portal-instance/div/div"))).click()
    bar.update(5)
    WebDriverWait(driver, 100).until(element_to_be_clickable((By.XPATH,
                                                              "/html/body/app/portal-ui/div/portal-dashboard/portal"
                                                              "-application-list/sso-expander/portal-instance-list/"
                                                              "div[1]/portal-instance/div/sso-expander/portal-profile-list"
                                                              "/div/portal-profile/span/span/span[2]/a"))).click()
    bar.update(6)
    WebDriverWait(driver, 100).until(presence_of_element_located((By.XPATH,
                                                                  "/html/body/app/portal-ui/div/portal-dashboard/portal-application-list/sso-expander/portal-instance-list/div[1]/portal-instance/div/sso-expander/portal-profile-list/div/portal-profile/span/span/span[2]/creds-modal/sso-modal/div/div/div[1]/h2")))
    bar.update(7)
    WebDriverWait(driver, 100).until(presence_of_element_located((By.XPATH,
                                                                  "//*[@class='code-line ng-tns-c19-8']")))
    bar.update(8)
    time.sleep(2)
    bar.update(9)
    elements = driver.find_elements_by_xpath("//*[@class='code-line ng-tns-c19-8']")
    bar.update(10)
    # AWS_ACCESS_KEY_ID
    cmd_aws_access_key_id = elements[0].get_attribute('innerText')
    print(cmd_aws_access_key_id + ";")
    aws_access_key_id = cmd_aws_access_key_id.split('"')[1]
    bar.update(11)
    # AWS_SECRET_ACCESS_KEY
    cmd_aws_secret_access_key = elements[1].get_attribute('innerText')
    print(cmd_aws_secret_access_key + ";")
    aws_secret_access_key = cmd_aws_secret_access_key.split('"')[1]
    bar.update(12)
    # AWS_SESSION_TOKEN
    cmd_aws_session_token = elements[2].get_attribute('innerText')
    print(cmd_aws_session_token + ";")
    aws_secret_session_token = cmd_aws_session_token.split('"')[1]
    bar.update(13)
    file = credentials_file
    profile_found = False
    with open(file, 'r+') as f:
        lines = f.readlines()  # read everything in the file
        f.seek(0)
        for i in range(len(lines)):
            line = lines[i]
            if not line.startswith('['):
                f.write(line)
            else:
                value_profile = line.split('[')[1].split(']')[0]
                if value_profile == profile:
                    profile_found = True
                    f.write(line)
                    f.write(f'aws_access_key_id="{aws_access_key_id}"' + "\n")
                    f.write(f'aws_secret_access_key="{aws_secret_access_key}"' + "\n")
                    f.write(f'aws_session_token="{aws_secret_session_token}"' + "\n")
                    i = i + 1
                    line = lines[i]
                    while i in range(len(lines)) and line not in ['\n', '\r\n'] and not line.startswith('[') and \
                            not line.startswith('aws_access_key_id=') and \
                            not line.startswith('aws_secret_access_key=') and \
                            not line.startswith('aws_session_token='):
                        f.write(line)
                        i = i + 1
                        line = lines[i]
                    if i in range(len(lines)) and line:
                        f.write(line)
                else:
                    f.write(line)
        if not profile_found:
            if len(lines) > 0:
                f.write("\n")
            f.write(f'[{profile}]' + "\n")
            f.write(f'aws_access_key_id="{aws_access_key_id}"' + "\n")
            f.write(f'aws_secret_access_key="{aws_secret_access_key}"' + "\n")
            f.write(f'aws_session_token="{aws_secret_session_token}"' + "\n")
    bar.update(15)


# Main method
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get cmd line variables')
    parser.add_argument('--profile', '-o', default='default', required=False, dest='profile',
                        help='Destination profile')
    parser.add_argument('--url', '-l', required=False, dest='url', help='AWS SSO URL')
    parser.add_argument('--username', '-u', required=False, dest='username', help='AWS SSO Username')
    parser.add_argument('--password', '-p', required=False, dest='password', help='AWS SSO Password')
    parser.add_argument('--aws-cred-file', '-f', required=False, dest='credentials_file', help='AWS Credentials file')
    args = parser.parse_args()
    aws_login_sso(args)
