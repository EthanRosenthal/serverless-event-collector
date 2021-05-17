# collector

A minimal API that receives events, forwards them to a Kinesis queue, and updates some event counters in DynamoDB.

[API docs](https://3o9x126nr7.execute-api.us-east-1.amazonaws.com/prod/docs)

The API is a [FastAPI](https://fastapi.tiangolo.com/) server. The app is instantiated in `collector.main`, and endpoints are defined in `collector.routers`. `collector.mangum` wraps the `FastAPI` application with a [Mangum](https://github.com/jordaneremieff/mangum) class which allows one to deploy the entire server as a Lambda function.


## The Makefile

The `Makefile` is largely used for automated testing in GitHub Actions, but you can also use it for building a virtual environment and running tests:

Create a virtual environment at `.venv/` and install both the app requirements and the dev requirements.
```commandline
make build
```

Run the tests
```commandline
make tests
```

Build and run tests
```commandline
make
```

Trigger a re-build
```commandline
make clean
make build
```

## Local development

Install app requirements

```commandline
pip install -r requirements.txt -r requirements-dev.txt
```

Run the server

```commandline
uvicorn collector.main:app
```

## Tests

```commandline
pytest tests/
```

