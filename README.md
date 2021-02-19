AWS SSO LOGIN
-----
Currently `aws sso login` is used to login to AWS OKTA and generate temporary credentials. But it does not support old .aws/credentials format which terraform still refers to as specified in bug [AWS_issue_10851](https://github.com/hashicorp/terraform-provider-aws/issues/10851)

  *  #### This script aims to update .aws/credentials file with the temporary credentials generated on SSO login
  *  #### Also this script automates login without needing to open a web browser
  *  #### Prints export commands as:
    *  export AWS_ACCESS_KEY_ID=123; export AWS_SECRET_ACCESS_KEY=123; export AWS_SESSION_TOKEN=123
  *  #### Saves variables to ~/.aws/credentials
    *  If profile is already defined it replaces existing value of access_key_id, secret_access_ky, session_token
    *  If profile does not exist it adds to file

### NOTE: This runs a selenium script to automate login flow in a headless chrome browser, hence may take upto a min to complete

# Prequisite

Install chromedriver

* In Mac ` brew install --cask chromedriver`

# Setup

1. `pip3 install -r requirements.txt`
2. Add this folder to your path - `export PATH=$PATH:aws_sso_login`

# Usage

1. Set environment variables as
    * export AWS_SSO_USERNAME=""
    * export AWS_SSO_PASSWORD=""

2. `eval $(aws_sso_login.py && inject_credentials.py)`

# Options

* There are two commands that are invoked by the single cmd - 'aws_sso_login'. However, these can be invoked separately
  as well:
    *  #### aws_sso_login.py
        * This automates web login via 'aws sso login'. It's options are
          - `aws_sso_login.py [-o|--profile profile] [-u|--username AWS_SSO_USERNMAE] [-p|--password AWS_SSO_PASSWORD]`
    *  #### inject_credentials.py
        * This injects credentials into ~/.aws/credentials and sets env variables *AWS_ACCESS_KEY_ID*, *
          AWS_SECRET_ACCESS_KEY* and *AWS_SESSION_TOKEN* from ~/.aws/cli/cache.
        * This can be invoked as - `inject_credentials.py [-h] [--profile PROFILE] [--aws-cred-file CREDENTIALS_FILE]`

#### All the arguments are optional

  *  #### 'default' is the default profile
  *  #### '~/.aws/credentials' is the default aws credentials file path
  *  #### the script can also access arguments via environment variables as
      *  export AWS_SSO_USERNAME=""
      *  export AWS_SSO_PASSWORD=""
      *  export AWS_CRED_FILE=""
  *  #### The precedence of picking up arguments is
      *  #### cmd-line arguments
      *  #### environment variables
      *  #### default values (for profile, credentials file)
   

# Tips

  *  This can be saved as an alias in your .bashrc or .zshrc : 

    `alias aws_sso_login='eval $(aws_sso_login.py && inject_credentials.py)'`
