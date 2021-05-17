from fastapi import Request


def get_username(request: Request) -> str:
    """The username gets added to the requestContext when the authorizer runs."""
    return request.scope["aws.event"]["requestContext"]["authorizer"]["username"]
