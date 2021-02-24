1. Separate inject_credentials into separate project/repo as folks may not use OKTA, but still may use inject_credentials.
2. Allow inject_credentials to be added to aws_sso_login, so people can combine  them if needed
3. Use GitHub Actions to build inject_credentials when aws_sso_login is also built
