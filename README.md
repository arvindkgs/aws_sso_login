AWS SSO LOGIN
-----
Currently `aws sso login` is used to login to AWS OKTA and generate temporary credentials. But it does not support old .aws/credentials format which terraform still refers to as specified in bug [AWS_issue_10851](https://github.com/hashicorp/terraform-provider-aws/issues/10851)

  *  #### This script aims to update .aws/credentials file with the temporary credentials generated on SSO login
  *  #### Injects AWS environment variables into your shell by running below cmds -
    *  export AWS_ACCESS_KEY_ID=123; export AWS_SECRET_ACCESS_KEY=123; export AWS_SESSION_TOKEN=123
  *  #### Updates given profile (defaults to `default` profile)
    *  If profile is already defined it replaces existing value of access_key_id, secret_access_ky, session_token
    *  If profile does not exist it adds to file


# Setup

1. Add this folder to your path - `export PATH=$PATH:aws_sso_login`

# Usage

1. `aws login sso`
2. `eval $(inject_credentials.py)` - this sets your shell up with AWS environment variables

# Options

*  #### inject_credentials.py
    * This injects credentials from ~/.aws/cli/cache into ~/.aws/credentials and sets env variables *AWS_ACCESS_KEY_ID*, *AWS_SECRET_ACCESS_KEY* and *AWS_SESSION_TOKEN* 
    * This can be invoked as - `inject_credentials.py [-h] [--profile PROFILE] [--aws-cred-file CREDENTIALS_FILE] [-v]`
    * `--profile` defaults to `default`
    * `--aws-cred-file` defaults to `~/.aws/credentials`
    * `-v` for verbose debug loggin

#### All the arguments are optional

  *  #### the script can also access arguments via environment variables as
      *  export AWS_CRED_FILE=""
  *  #### The precedence of picking up arguments is
      *  #### cmd-line arguments
      *  #### environment variables
      *  #### default values (for profile, credentials file)
   

# Recommendations

  *  If using iTerm2, 
      *  Create profile that runs shell cmd at startup - `eval $(inject_credentials.py)`
      *  When using multiple tabs, instead of running `eval $(inject_credentials.py)` for each tab, close iTerm2, and reopen it. This causes all tabs to reopen and also run the `eval $(inject_credentials.py)` script on startup
