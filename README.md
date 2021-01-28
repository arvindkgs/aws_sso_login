AWS SSO LOGIN
-----
Currently `aws sso login` is used to login to AWS OKTA and generate temporary credentials. But it does not support old .aws/credentials format which terraform still refers to as specified in bug [AWS_issue_10851](https://github.com/hashicorp/terraform-provider-aws/issues/10851)
  *  #### This script aims to update .aws/credentials file with the temporary credentials generated on SSO login
  *  #### Also this script automates login without needing to open a web browser

Script that automates login to AWS OKTA SSO and

  1.  Prints export commands as:

    *  export AWS_ACCESS_KEY_ID=123; export AWS_SECRET_ACCESS_KEY=123; export AWS_SESSION_TOKEN=123

  2.  also saves variables to ~/.aws/credentials

    1.  If profile is already defined it replaces existing value of access_key_id, secret_access_key, session_token
    2.  If profile does not exist it adds to file

# Prequisite

Install chromedriver

  * In Mac ` brew install --cask chromedriver`

# Install

  * `pip install dist/aws_sso_login-0.0.1-py3-none-any.whl`

# Usage

`python -m aws_sso_login [-o|--profile profile] [-l|--url AWS_SSO_URL] [-u|--username AWS_SSO_USERNMAE] [-p|--password AWS_SSO_PASSWORD] [-f|--aws-cred-file AWS_CRED_FILE]`

#### All the arguments are optional

  *  #### 'default' is the default profile
  *  #### '~/.aws/credentials' is the default aws credentials file path
  *  #### the script can also access arguments via environment variables as
    *  export AWS_SSO_USERNAME=""
    *  export AWS_SSO_PASSWORD=""
    *  export AWS_SSO_URL=""
    *  export AWS_CRED_FILE=""
  *  #### The precedence of picking up arguments is
    *  #### cmd-line arguments
    *  #### environment variables
    *  #### default values (for profile, credentials file)
   

# Tips
  *  Running below command also sets the env variables on the current shell (before running command, edit it to show full path to "aws_sso_login.py") 

  `eval $(python -m aws_sso_login)`

  *  This can be saved as an alias in your .bashrc or .zshrc : 

  `alias aws_sso_login='eval $(python -m aws_sso_login)`

# Build
  To make change and build,
  1.  `python -m pip install setuptools wheel`
  2.  `python setup.py sdist bdist_wheel`
  
  This will generate the dist folder containing the .whl artifact that can be install by running - `pip install aws_sso_login-0.0.1-py3-none-any.whl`
