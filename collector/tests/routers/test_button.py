from unittest import mock

from moto import mock_dynamodb2
import pytest

from collector.routers import button


@pytest.fixture(scope="function")
def setup_dynamo():
    with mock_dynamodb2():
        button.ButtonClickCounter.create_table(wait=True)
        button.ButtonClickCounter(username="test-user", button_id="ABC", count=5).save()
        yield


"""
Button Click POST Tests
"""


@mock.patch.object(button, "put_record")
@mock.patch.object(button, "get_username")
@mock.patch.object(button.time, "time")
def test_button_click_success(
    mock_time, mock_get_user, mock_put_record, test_app, setup_dynamo
):
    mock_time.return_value = 123
    mock_get_user.return_value = "test-user"

    payload = {"session_id": "XYZ", "button_id": "ABC"}
    response = test_app.post("/button/click", json=payload)

    assert response.status_code == 200
    mock_put_record.assert_called_with(
        {
            "session_id": "XYZ",
            "button_id": "ABC",
            "username": "test-user",
            "event_type": "button_click",
            "received_at": 123_000,
        }
    )
    assert button.ButtonClickCounter.get("test-user", "ABC").count == 6


@mock.patch.object(button, "put_record")
@mock.patch.object(button, "get_username")
def test_button_click_new_user(mock_get_user, mock_put_record, test_app, setup_dynamo):
    mock_get_user.return_value = "new-user"

    payload = {"session_id": "XYZ", "button_id": "ABC"}
    response = test_app.post("/button/click", json=payload)

    assert response.status_code == 200
    assert button.ButtonClickCounter.get("new-user", "ABC").count == 1


def test_button_click_success_bad_put(test_app, setup_dynamo):
    payload = {"session_id": "XYZ", "button_id": "ABC"}
    with mock.patch.object(button, "put_record") as put_record:
        put_record.return_value = False
        response = test_app.post("/button/click", json=payload)
        assert response.status_code == 500


def test_button_click_success_bad_payload(test_app, setup_dynamo):
    payload = {"button_id": "ABC"}
    with mock.patch.object(button, "put_record") as put_record:
        put_record.return_value = False
        response = test_app.post("/button/click", json=payload)
        assert response.status_code == 422


"""
Button Click Count Tests
"""


@mock.patch.object(button, "get_username")
def test_button_click_counts_success(mock_get_user, test_app, setup_dynamo):
    mock_get_user.return_value = "test-user"
    payload = {"button_id": "ABC"}
    response = test_app.get("/button/click/count", params=payload)
    assert response.status_code == 200
    assert response.json() == {"count": 5}


def test_button_click_counts_no_username(test_app, setup_dynamo):
    payload = {"button_id": "ABC"}
    response = test_app.get("/button/click/count", params=payload)
    assert response.status_code == 200
    assert response.json() == {"count": 0}


@mock.patch.object(button, "get_username")
def test_button_click_counts_user_not_found(mock_get_user, test_app, setup_dynamo):
    mock_get_user.return_value = "MISSING-USER"
    payload = {"button_id": "ABC"}
    response = test_app.get("/button/click/count", params=payload)
    assert response.status_code == 200
    assert response.json() == {"count": 0}


@mock.patch.object(button, "get_username")
def test_button_click_counts_unknown_button(mock_get_user, test_app, setup_dynamo):
    mock_get_user.return_value = "test-user"
    payload = {"button_id": "MISSING"}
    response = test_app.get("/button/click/count", params=payload)
    assert response.status_code == 200
    assert response.json() == {"count": 0}
