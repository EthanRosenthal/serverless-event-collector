from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware

from collector.routers import web, button

tags_metadata = [
    {"name": "web", "description": "General website product analytics"},
    {"name": "button", "description": "Operations related to clicking buttons"},
]

app = FastAPI(
    title="Serverless Event Collector",
    description=(
        "A minimal API for collecting web analytics events. This API is for"
        " demonstration purposes to show an implementation of a serverless setup for"
        " collecting events."
    ),
    version="0.1.0",
    openapi_tags=tags_metadata,
    docs_url=None,
    redoc_url="/docs",
)
app.include_router(web.router)
app.include_router(button.router)

# Some copy pasta from https://github.com/chgangaraju/fastapi-mangum-example/blob/master/app/main.py
# Seems to allow me to query using client side javascript
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def hello_world():
    return {"message": "Hello World"}


# Below is taken from
# https://github.com/jordaneremieff/mangum/issues/147#issuecomment-795857251
# The code is needed to set the FastAPI root_path to contain the stage that serverless
# deploys the API to (e.g. /dev). Specifically, the middleware below ensures that the
# docs will be served correctly.


@app.middleware("http")
async def set_root_path_for_api_gateway(request: Request, call_next):
    """Sets the FastAPI root_path dynamically from the ASGI request data."""

    root_path = request.scope["root_path"]
    if root_path:
        # Assume set correctly in this case
        app.root_path = root_path

    else:
        # fetch from AWS requestContext
        if "aws.event" in request.scope:
            context = request.scope["aws.event"]["requestContext"]

            if "customDomain" not in context:
                root_path = f"/{context['stage']}"

                if request.scope["path"].startswith(root_path):
                    request.scope["path"] = request.scope["path"][len(root_path) :]
                request.scope["root_path"] = root_path
                app.root_path = root_path

    response = await call_next(request)
    return response
