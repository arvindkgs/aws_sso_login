AWS SSO LOGIN
-----
Script that automates login to AWS OKTA SSO and

  1.  Prints export commands as:

    *  export AWS_ACCESS_KEY_ID=123; export AWS_SECRET_ACCESS_KEY=123; export AWS_SESSION_TOKEN=123
    *  This can be added to shell by :
       `eval $(aws_sso_login)`

  2.  also saves variables to ~/.aws/credentials

    1.  If profile is already defined it replaces existing value of access_key_id, secret_access_key, session_token
    2.  If profile does not exist it adds to file

# Prequisite

Install chromedriver

* In Mac ` brew install --cask chromedriver`

# Usage

`aws_sso_login [-o|--profile profile] [-l|--url AWS_SSO_URL] [-u|--username AWS_SSO_USERNMAE] [-p|--password AWS_SSO_PASSWORD] [-f|--aws-cred-file AWS_CRED_FILE]`

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
*  Running below command also sets the env variables on the current shell  
`eval $(aws_sso_login)`
*  This can be saved as an alias in your .bashrc or .zshrc
`alias aws_sso_login='eval $(aws_sso_login)`
