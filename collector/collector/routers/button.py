import time

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from pynamodb.exceptions import DoesNotExist, TableDoesNotExist

from collector.context_utils import get_username
from collector.dynamo import ButtonClickCounter, update_count
from collector.kinesis import put_record

router = APIRouter(prefix="/button")


class ButtonClick(BaseModel):
    session_id: str
    button_id: str


@router.post("/click", tags=["button"])
def button_click(button_click: ButtonClick, request: Request):
    record = button_click.dict()
    username_provided = False
    try:
        record["username"] = get_username(request)
        username_provided = True
    except KeyError:
        pass
    record["event_type"] = "button_click"
    record["received_at"] = int(time.time() * 1_000)  # Milliseconds since Unix epoch
    success = put_record(record)
    if success:
        if username_provided:
            update_count(ButtonClickCounter, record["username"], record["button_id"])
        return {"message": "Received"}
    else:
        raise HTTPException(status_code=500, detail="Unknown error")


@router.get("/click/count", tags=["button"])
def button_click_counts(button_id: str, request: Request):
    try:
        username = get_username(request)
    except KeyError:
        return {"count": 0}

    try:
        return {"count": ButtonClickCounter.get(username, button_id).count}
    except (DoesNotExist, TableDoesNotExist):
        return {"count": 0}
