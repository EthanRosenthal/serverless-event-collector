import datetime as dt
from unittest import mock

import main


def dt_to_epoch_ms(datetime_):
    return datetime_.replace(tzinfo=dt.timezone.utc).timestamp() * 1_000


class TestS3LocationMapper:
    def _default_event(self):
        return {
            "session_id": "XYZ",
            "button_id": "ABC",
        }

    def test_get_bucket(self):
        mgr = main.S3LocationMapper()
        bucket = mgr.get_bucket("test")
        assert bucket == "test-raw-events"

    def test_put_event_with_new_path(self):
        mgr = main.S3LocationMapper()
        event = self._default_event()
        event["received_at"] = dt_to_epoch_ms(dt.datetime(2021, 2, 1, 0, 1))
        mock_uuid = "some_uuid"

        with mock.patch.object(
            main.uuid, "uuid4", return_value=mock_uuid
        ) as mock_uuid_function:
            mgr.add(event, "test", "button_click")

        expected_bucket = "test-raw-events"
        expected_path = "button_click/year=2021/month=2/day=1/hour=0"
        expected_key = f"{expected_path}/records-2021-02-01-00-01-00-{mock_uuid}"

        expected_locations = {(expected_bucket, expected_path): expected_key}
        assert mgr.locations == expected_locations

        expected_event_store = {(expected_bucket, expected_key): [event]}
        assert mgr.event_store == expected_event_store

    def test_put_two_events_with_same_path_for_same_user(self):
        mgr = main.S3LocationMapper()
        first_event = self._default_event()
        first_event["received_at"] = dt_to_epoch_ms(dt.datetime(2021, 2, 1, 0, 1))

        second_event = self._default_event()
        second_event["received_at"] = dt_to_epoch_ms(dt.datetime(2021, 2, 1, 0, 1, 1))

        mock_uuid = "some_uuid"

        with mock.patch.object(
            main.uuid, "uuid4", return_value=mock_uuid
        ) as mock_uuid_function:
            mgr.add(first_event, "test", "button_click")
            mgr.add(second_event, "test", "button_click")

        expected_bucket = "test-raw-events"
        expected_path = "button_click/year=2021/month=2/day=1/hour=0"
        expected_key = f"{expected_path}/records-2021-02-01-00-01-00-{mock_uuid}"

        expected_locations = {(expected_bucket, expected_path): expected_key}
        assert mgr.locations == expected_locations

        expected_event_store = {
            (expected_bucket, expected_key): [first_event, second_event]
        }
        assert mgr.event_store == expected_event_store

    def test_put_two_events_with_different_paths_for_same_user(self):
        mgr = main.S3LocationMapper()
        first_event = self._default_event()
        first_event["received_at"] = dt_to_epoch_ms(dt.datetime(2021, 2, 1, 0, 1))

        second_event = self._default_event()
        second_event["received_at"] = dt_to_epoch_ms(dt.datetime(2021, 2, 1, 1, 1, 1))

        first_uuid = "GGG"
        second_uuid = "HHH"

        with mock.patch.object(
            main.uuid, "uuid4", side_effect=[first_uuid, second_uuid]
        ) as mock_uuid_function:
            mgr.add(first_event, "test", "button_click")
            mgr.add(second_event, "test", "button_click")

        expected_bucket = "test-raw-events"
        first_path = "button_click/year=2021/month=2/day=1/hour=0"
        second_path = "button_click/year=2021/month=2/day=1/hour=1"
        first_key = f"{first_path}/records-2021-02-01-00-01-00-{first_uuid}"
        second_key = f"{second_path}/records-2021-02-01-01-01-01-{second_uuid}"

        expected_locations = {
            (expected_bucket, first_path): first_key,
            (expected_bucket, second_path): second_key,
        }
        assert mgr.locations == expected_locations

        expected_event_store = {
            (expected_bucket, first_key): [first_event],
            (expected_bucket, second_key): [second_event],
        }
        assert mgr.event_store == expected_event_store

    def test_put_two_events_with_same_path_for_different_users(self):
        mgr = main.S3LocationMapper()
        first_event = self._default_event()
        first_event["received_at"] = dt_to_epoch_ms(dt.datetime(2021, 2, 1, 0, 1))

        second_event = self._default_event()
        second_event["username"] = "new-user"
        second_event["received_at"] = dt_to_epoch_ms(dt.datetime(2021, 2, 1, 1, 1, 1))

        first_uuid = "GGG"
        second_uuid = "HHH"

        with mock.patch.object(
            main.uuid, "uuid4", side_effect=[first_uuid, second_uuid]
        ) as mock_uuid_function:
            mgr.add(first_event, "test", "button_click")
            mgr.add(second_event, "new-user", "button_click")

        first_bucket = "test-raw-events"
        second_bucket = "new-user-raw-events"
        first_path = "button_click/year=2021/month=2/day=1/hour=0"
        second_path = "button_click/year=2021/month=2/day=1/hour=1"
        first_key = f"{first_path}/records-2021-02-01-00-01-00-{first_uuid}"
        second_key = f"{second_path}/records-2021-02-01-01-01-01-{second_uuid}"

        expected_locations = {
            (first_bucket, first_path): first_key,
            (second_bucket, second_path): second_key,
        }
        assert mgr.locations == expected_locations

        expected_event_store = {
            (first_bucket, first_key): [first_event],
            (second_bucket, second_key): [second_event],
        }
        assert mgr.event_store == expected_event_store
