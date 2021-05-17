from base64 import b64encode
from urllib.parse import quote

import main


def encode(username, password):
    """Returns an HTTP basic authentication encrypted string given a valid
    username and password.
    """

    username_password = "%s:%s" % (quote(username), quote(password))
    return "Basic " + b64encode(username_password.encode()).decode()


def test_decode():
    username, password = main.decode(encode("username", "password"))
    assert username == "username"
    assert password == "password"


def test_arn_endpoint_wildcard():
    arn = "arn:aws:execute-api:us-east-1:0000000000:XXXYYY/stage/POST/some/endpoint"
    expected = "arn:aws:execute-api:us-east-1:0000000000:XXXYYY/stage/POST/*"
    assert main.arn_endpoint_wildcard(arn) == expected


class Test_handler:
    def test_is_authorized(self):
        authorization = encode("ethan", "xyz")
        event = {
            "methodArn": "arn:aws:execute-api:us-east-1:0000000000:XXXYYY/stage/POST/some/endpoint",
            "headers": {"Authorization": authorization},
        }
        result = main.handler(event, {})
        expected = {
            "principalId": "ethan",
            "policyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "execute-api:Invoke",
                        "Effect": "Allow",
                        "Resource": "arn:aws:execute-api:us-east-1:0000000000:XXXYYY/stage/POST/*",
                    }
                ],
            },
            "usageIdentifierKey": authorization,
            "context": {"username": "ethan"},
        }
        assert result == expected

    def test_denied(self):
        authorization = encode("not-ethan", "xyz")
        event = {
            "methodArn": "arn:aws:execute-api:us-east-1:0000000000:XXXYYY/stage/POST/some/endpoint",
            "headers": {"Authorization": authorization},
        }
        result = main.handler(event, {})
        expected = {
            "principalId": "not-ethan",
            "policyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "execute-api:Invoke",
                        "Effect": "Deny",
                        "Resource": "arn:aws:execute-api:us-east-1:0000000000:XXXYYY/stage/POST/*",
                    }
                ],
            },
            "usageIdentifierKey": authorization,
        }
        assert result == expected
