from base64 import b64decode, b64encode
import logging
from typing import Optional
from urllib.parse import unquote, quote


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def is_authorized(username: str, api_key: str) -> bool:
    # Do a lookup in Secrets Manager.

    # But I'm cheap and don't want to pay for that for this demo, so we instead hardcode
    # the usernames and api keys right here.
    hardcoded_map = {"ethan": "xyz"}
    try:
        return hardcoded_map[username] == api_key
    except KeyError:
        return False


"""
Below region is stolen from 
https://github.com/rdegges/python-basicauth/blob/master/basicauth.py
"""


class DecodeError(Exception):
    pass


class EncodeError(Exception):
    pass


def decode(encoded_str):
    """Decode an encrypted HTTP basic authentication string. Returns a tuple of
    the form (username, password), and raises a DecodeError exception if
    nothing could be decoded.
    """
    split = encoded_str.strip().split(" ")

    # If split is only one element, try to decode the username and password
    # directly.
    if len(split) == 1:
        try:
            username, password = b64decode(split[0]).decode().split(":", 1)
        except:
            raise DecodeError

    # If there are only two elements, check the first and ensure it says
    # 'basic' so that we know we're about to decode the right thing. If not,
    # bail out.
    elif len(split) == 2:
        if split[0].strip().lower() == "basic":
            try:
                username, password = b64decode(split[1]).decode().split(":", 1)
            except:
                raise DecodeError
        else:
            raise DecodeError

    # If there are more than 2 elements, something crazy must be happening.
    # Bail.
    else:
        raise DecodeError

    return unquote(username), unquote(password)


"""
End stolen region
"""


def generate_auth_response(
    principal_id: str,
    usage_identifier_key: Optional[str],
    context: Optional[dict],
    effect: str,
    resource: str,
) -> dict:
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {"Action": "execute-api:Invoke", "Effect": effect, "Resource": resource}
        ],
    }
    auth_response = {"principalId": principal_id, "policyDocument": policy_document}
    if usage_identifier_key is not None:
        auth_response["usageIdentifierKey"] = usage_identifier_key
    if context is not None:
        auth_response["context"] = context
    return auth_response


def arn_endpoint_wildcard(arn: str) -> str:
    """
    Take an arn containing a full path of endpoints and
    return the arn with a wildcard for all endpoints

    Example
    -------
    input: arn:aws:execute-api:us-east-1:0000000000:XXXYYY/stage/POST/some/endpoint
    output: arn:aws:execute-api:us-east-1:0000000000:XXXYYY/stage/POST/*
    """
    stripped_arn = "/".join(arn.split("/")[0:3])
    return f"{stripped_arn}/*"


def handler(event: dict, lambda_context: dict) -> dict:
    arn = arn_endpoint_wildcard(event["methodArn"])

    auth_header = event["headers"].get("Authorization")
    username, provided_api_key = decode(auth_header)

    if is_authorized(username, provided_api_key):
        context = {"username": username}
        logger.info("Success! Generating auth response")
        return generate_auth_response(username, auth_header, context, "Allow", arn)
    else:
        logger.info("User is not authorized")
        return generate_auth_response(username, auth_header, None, "Deny", arn)
