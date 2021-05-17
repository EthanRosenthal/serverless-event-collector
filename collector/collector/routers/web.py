import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from pynamodb.exceptions import DoesNotExist, TableDoesNotExist

from collector.context_utils import get_username
from collector.dynamo import PageViewCounter, update_count
from collector.kinesis import put_record

router = APIRouter(prefix="/web")


class PageView(BaseModel):
    url: str
    referral_url: Optional[str]
    ipaddress: Optional[str]
    useragent: Optional[str]
    session_id: str


@router.post("/page_view", tags=["web"])
def page_view(page_view: PageView, request: Request):
    record = page_view.dict()
    username_provided = False
    try:
        record["username"] = get_username(request)
        username_provided = True
    except KeyError:
        pass
    record["event_type"] = "page_view"
    record["received_at"] = int(time.time() * 1_000)  # Milliseconds since Unix epoch
    success = put_record(record)
    if success:
        if username_provided:
            update_count(PageViewCounter, record["username"], record["url"])
        return {"message": "Received"}
    else:
        raise HTTPException(status_code=500, detail="Unknown error")


@router.get("/page_view/count", tags=["web"])
def page_view_counts(url: str, request: Request):
    try:
        username = get_username(request)
    except KeyError:
        return {"count": 0}

    try:
        return {"count": PageViewCounter.get(username, url).count}
    except (DoesNotExist, TableDoesNotExist):
        return {"count": 0}
