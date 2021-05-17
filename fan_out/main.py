from collections import Counter, defaultdict
import datetime as dt
from functools import lru_cache
import json
import logging
from typing import cast, Dict, List, Tuple, Optional
import os
import urllib
import uuid

import boto3
from botocore.client import ClientError
from pynamodb.models import DoesNotExist, Model
from pynamodb.attributes import NumberAttribute, UnicodeAttribute

logger = logging.getLogger()
logger.setLevel(logging.INFO)


ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")


class EventCounter(Model):
    """
    An event counter model
    """

    class Meta:
        table_name = f"{ENVIRONMENT}-event-counter"

    username = UnicodeAttribute(hash_key=True)
    event_name = UnicodeAttribute(range_key=True)
    count = NumberAttribute(default=0)


def update_dynamo(counter: Counter) -> None:
    if not EventCounter.exists():
        EventCounter.create_table(billing_mode="PAY_PER_REQUEST", wait=True)

    for (username, event_name), count in counter.items():
        try:
            event_counter = EventCounter.get(username, event_name)
        except DoesNotExist:
            event_counter = EventCounter(username, event_name)
            event_counter.save()
        # Increment the count
        event_counter.update(
            actions=[EventCounter.count.set(EventCounter.count + count)]  # type: ignore
        )


class EventParseError(BaseException):
    """Exception in parsing event"""


class S3LocationMapper:
    def __init__(self):
        self.locations: Dict[Tuple[str, str], str] = {}
        self.event_store: Dict[Tuple[str, str], List[dict]] = defaultdict(list)

    @staticmethod
    def get_bucket(username: str) -> str:
        return f"{username}-raw-events"

    def _construct_path(self, event_type: str, timestamp: dt.datetime) -> str:
        path = (
            f"{event_type}"
            f"/year={timestamp.year}"
            f"/month={timestamp.month}"
            f"/day={timestamp.day}"
            f"/hour={timestamp.hour}"
        )
        return path

    @staticmethod
    def parse_timestamp(event: dict) -> dt.datetime:
        received_at = event["received_at"]
        try:
            timestamp = dt.datetime.utcfromtimestamp(received_at / 1000)
        except Exception as e:
            logger.exception("Unknown error constructing timestamp")
            raise EventParseError(e)

        return timestamp

    def add(self, event: dict, username: str, event_type: str) -> None:
        timestamp = self.parse_timestamp(event)
        bucket = self.get_bucket(username)
        path = self._construct_path(event_type, timestamp)
        if (bucket, path) in self.locations:
            key = self.locations[(bucket, path)]
        else:
            key = (
                f"{path}/records-{timestamp.year:04d}-{timestamp.month:02d}-"
                f"{timestamp.day:02d}-{timestamp.hour:02d}-{timestamp.minute:02d}-"
                f"{timestamp.second:02d}-{str(uuid.uuid4())}"
            )
            self.locations[(bucket, path)] = key

        self.event_store[(bucket, key)].append(event)


@lru_cache(maxsize=32)
def bucket_exists(bucket_name: str) -> bool:
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(bucket_name)
    try:
        s3.meta.client.head_bucket(Bucket=bucket.name)
        exists = True
    except ClientError:
        exists = False
    return exists


def put_events(events: List[dict], bucket: str, key: str) -> None:
    s3_client = boto3.client("s3")
    if not bucket_exists(bucket):
        logger.exception(f"No bucket found for bucket {bucket}")
        # TODO: Throw them into a "not found" bin.
        return
    body = "\n".join(json.dumps(e) for e in events)
    body = body.rstrip("\n")
    s3_client.put_object(
        Bucket=bucket, Key=key, Body=body, ContentType="application/json"
    )


def download_key(bucket: str, key: str) -> List[str]:
    s3_client = boto3.client("s3")
    response = s3_client.get_object(Bucket=bucket, Key=key)
    body = response["Body"].read()
    # Convert to string
    body = body.decode("utf-8")
    # There will always be a trailing newline
    body = body.rstrip("\n")
    # Now, split up each event into its own json string
    body = body.split("\n")
    return body


def handler(lambda_event: dict, lambda_context: dict) -> None:
    source_bucket = lambda_event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(lambda_event["Records"][0]["s3"]["object"]["key"])
    logger.info(f"Reading {key} from {source_bucket}")

    events = download_key(source_bucket, key)
    loc_mapper = S3LocationMapper()
    counter: Counter = Counter()

    for event_string in events:
        try:
            event: dict = cast(dict, json.loads(event_string))
        except json.JSONDecodeError:
            logger.exception("Failed to load decode event")
            continue

        try:
            event_type = event.pop("event_type")
            username = event.pop("username")
        except KeyError:
            logger.exception(f"Missing required key for event {event}")
            continue

        loc_mapper.add(event, username, event_type)
        counter[(username, event_type)] += 1

    update_dynamo(counter)

    for (bucket, key), events in loc_mapper.event_store.items():
        try:
            put_events(events, bucket, key)
        except:
            logger.exception(f"Unknown error putting events in {bucket}/{key}")
