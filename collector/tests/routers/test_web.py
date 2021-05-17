from unittest import mock

from moto import mock_dynamodb2
import pytest

from collector.routers import web


@pytest.fixture(scope="function")
def setup_dynamo():
    with mock_dynamodb2():
        web.PageViewCounter.create_table(wait=True)
        web.PageViewCounter(
            username="test-user", url="http://something.com", count=5
        ).save()
        yield


"""
Page View POST Tests
"""


@mock.patch.object(web, "put_record")
@mock.patch.object(web, "get_username")
@mock.patch.object(web.time, "time")
def test_page_view_success(
    mock_time, mock_get_user, mock_put_record, test_app, setup_dynamo
):
    mock_time.return_value = 123
    mock_get_user.return_value = "test-user"

    payload = {
        "url": "http://something.com",
        "referral_url": "/",
        "useragent": "some-string",
        "session_id": "XYZ",
    }
    response = test_app.post("/web/page_view", json=payload)

    assert response.status_code == 200
    mock_put_record.assert_called_with(
        {
            "url": "http://something.com",
            "referral_url": "/",
            "ipaddress": None,
            "useragent": "some-string",
            "session_id": "XYZ",
            "username": "test-user",
            "event_type": "page_view",
            "received_at": 123_000,
        }
    )
    assert web.PageViewCounter.get("test-user", "http://something.com").count == 6


@mock.patch.object(web, "put_record")
@mock.patch.object(web, "get_username")
def test_page_view_new_user(mock_get_user, mock_put_record, test_app, setup_dynamo):
    mock_get_user.return_value = "new-user"

    payload = {
        "url": "http://something.com",
        "referral_url": "/",
        "useragent": "some-string",
        "session_id": "XYZ",
    }
    response = test_app.post("/web/page_view", json=payload)

    assert response.status_code == 200
    assert web.PageViewCounter.get("new-user", "http://something.com").count == 1


def test_page_view_success_bad_put(test_app):
    payload = {
        "url": "http://something.com",
        "referral_url": "/",
        "useragent": "some-string",
        "session_id": "XYZ",
    }
    with mock.patch.object(web, "put_record") as put_record:
        put_record.return_value = False
        response = test_app.post("/web/page_view", json=payload)
        assert response.status_code == 500


def test_page_view_success_bad_payload(test_app):
    payload = {"referral_url": "/", "useragent": "some-string", "session_id": "XYZ"}
    with mock.patch.object(web, "put_record") as put_record:
        put_record.return_value = False
        response = test_app.post("/web/page_view", json=payload)
        assert response.status_code == 422


"""
Page View Count Tests
"""


@mock.patch.object(web, "get_username")
def test_page_view_counts_success(mock_get_user, test_app, setup_dynamo):
    mock_get_user.return_value = "test-user"
    payload = {
        "url": "http://something.com",
        "referral_url": "/",
        "useragent": "some-string",
        "session_id": "XYZ",
    }
    response = test_app.get("/web/page_view/count", params=payload)
    assert response.status_code == 200
    assert response.json() == {"count": 5}


def test_page_view_counts_no_username(test_app, setup_dynamo):
    payload = {
        "url": "http://something.com",
        "referral_url": "/",
        "useragent": "some-string",
        "session_id": "XYZ",
    }
    response = test_app.get("/web/page_view/count", params=payload)
    assert response.status_code == 200
    assert response.json() == {"count": 0}


@mock.patch.object(web, "get_username")
def test_page_view_counts_user_not_found(mock_get_user, test_app, setup_dynamo):
    mock_get_user.return_value = "MISSING-USER"
    payload = {
        "url": "http://something.com",
        "referral_url": "/",
        "useragent": "some-string",
        "session_id": "XYZ",
    }
    response = test_app.get("/web/page_view/count", params=payload)
    assert response.status_code == 200
    assert response.json() == {"count": 0}


@mock.patch.object(web, "get_username")
def test_page_view_counts_unknown_url(mock_get_user, test_app, setup_dynamo):
    mock_get_user.return_value = "test-user"
    payload = {
        "url": "http://some-other-url.com",
        "referral_url": "/",
        "useragent": "some-string",
        "session_id": "XYZ",
    }
    response = test_app.get("/web/page_view/count", params=payload)
    assert response.status_code == 200
    assert response.json() == {"count": 0}
