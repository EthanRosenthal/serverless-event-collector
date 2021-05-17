import os

from pynamodb.models import DoesNotExist, Model
from pynamodb.attributes import NumberAttribute, UnicodeAttribute


ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")


class PageViewCounter(Model):
    """
    Track page views
    """

    class Meta:
        table_name = f"{ENVIRONMENT}-page-view-counter"

    username = UnicodeAttribute(hash_key=True)
    url = UnicodeAttribute(range_key=True)
    count = NumberAttribute(default=0)
