# authorizer

A Lambda function that authorizes requests to the `collector`. Requests should be sent using basic auth. The allowed usernames and passwords are hardcoded into the lambda function for demonstration purposes. In practice, you would want to rely on [Secrets Manager](https://aws.amazon.com/secrets-manager/) or something like that.

The authorizer also forwards the username to `collector` via the `requestContext` field.
