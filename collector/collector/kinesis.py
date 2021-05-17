import json
import logging
import os

import boto3

logger = logging.getLogger(__name__)

KINESIS_STREAM = os.environ.get("KINESIS_STREAM", "dev")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")


def put_record(record: dict) -> bool:
    kinesis_client = boto3.client("firehose", region_name=AWS_REGION)
    put_response = kinesis_client.put_record(
        DeliveryStreamName=KINESIS_STREAM, Record={"Data": json.dumps(record) + "\n"}
    )
    success = put_response["ResponseMetadata"]["HTTPStatusCode"] == 200
    if not success:
        logger.exception(put_response)
    return success
