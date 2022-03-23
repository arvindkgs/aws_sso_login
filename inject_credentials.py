#!/usr/bin/python3
import json
import logging
import os
from pathlib import Path
import argparse
import sys

"""
This Python script copies creds from ~/.aws/cli/cache/*.json to ~/.aws/credentials
"""


def inject_credentials(args):
    logger = logging.getLogger("inject_credentials")
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    credentials_file = args.credentials_file
    profile = args.profile
    if not credentials_file:
        credentials_file = os.environ.get('AWS_CRED_FILE')
        if not credentials_file:
            logger.debug("Updating '~/.aws/credentials'")
            credentials_file = "~/.aws/credentials"
        else:
            logger.debug("Updating 'AWS_CRED_FILE' from env")
    files = sorted(Path(os.path.expanduser("~/.aws/cli/cache")).iterdir(), key=os.path.getmtime)
    if len(files) > 0:
        with open(files[0], 'r') as creds:
            logger.debug('Reading file: ' + creds.name)
            readFile = creds.read()
            cached_creds = json.loads(readFile)
            # AWS_ACCESS_KEY_ID
            aws_access_key_id = cached_creds['Credentials'].get('AccessKeyId')
            print(f'export AWS_ACCESS_KEY_ID="{aws_access_key_id}";')
            # AWS_SECRET_ACCESS_KEY
            aws_secret_access_key = cached_creds['Credentials'].get('SecretAccessKey')
            print(f'export AWS_SECRET_ACCESS_KEY="{aws_secret_access_key}";')
            # AWS_SESSION_TOKEN
            aws_secret_session_token = cached_creds['Credentials'].get('SessionToken')
            print(f'export AWS_SESSION_TOKEN="{aws_secret_session_token}";')
            file = os.path.expanduser(credentials_file)
            if not os.path.exists(file):
                with open(file, 'w') as f:
                    logger.debug("Creating file: " + f.name)
                    f.write(f'[{profile}]' + "\n")
                    write_aws_creds(aws_access_key_id, aws_secret_access_key, aws_secret_session_token, f)
            else:
                in_profile = False
                written_creds = False
                with open(file, 'r+') as f:
                    logger.debug('Editing file: ' + f.name)
                    lines = f.readlines()  # read everything in the file
                    f.seek(0)
                    i = 0
                    while i < len(lines):
                        line = lines[i]
                        logger.debug(f'{line}')
                        if line in ['\n', '\r\n']:
                            in_profile = False
                        elif line.startswith('['):
                            value_profile = line.split('[')[1].split(']')[0]
                            if value_profile == profile:
                                in_profile = True
                                f.write(line)
                                write_aws_creds(aws_access_key_id, aws_secret_access_key, aws_secret_session_token, f)
                                written_creds = True
                                logger.debug('writing aws keys')
                                i += 1
                                continue
                            else:
                                in_profile = False
                        elif (line.startswith('aws_access_key_id=') or \
                              line.startswith('aws_secret_access_key=') or \
                              line.startswith('aws_session_token=')) and in_profile:
                            logger.debug('skipping')
                            i += 1
                            continue
                        f.write(line)
                        i += 1
                    if not written_creds:
                        f.write('\n')
                        f.write(f'[{profile}]' + "\n")
                        write_aws_creds(aws_access_key_id, aws_secret_access_key, aws_secret_session_token, f)
                    f.truncate()


def write_aws_creds(aws_access_key_id, aws_secret_access_key, aws_secret_session_token, f):
    f.write(f'aws_access_key_id="{aws_access_key_id}"' + "\n")
    f.write(f'aws_secret_access_key="{aws_secret_access_key}"' + "\n")
    f.write(f'aws_session_token="{aws_secret_session_token}"' + "\n")


# Main method
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get cmd line variables')
    parser.add_argument('--profile', '-o', default='default', required=False, dest='profile',
                        help='Destination profile')
    parser.add_argument('--aws-cred-file', '-f', required=False, dest='credentials_file', help='AWS_CRED_FILE')
    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                    action="store_true")
    args = parser.parse_args()
    inject_credentials(args)
