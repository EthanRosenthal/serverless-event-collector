import os

from pynamodb.models import Model
from pynamodb.attributes import NumberAttribute, UnicodeAttribute


ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")


class ButtonClickCounter(Model):
    """
    Track button clicks
    """

    class Meta:
        table_name = f"{ENVIRONMENT}-button-click-counter"

    username = UnicodeAttribute(hash_key=True)
    button_id = UnicodeAttribute(range_key=True)
    count = NumberAttribute(default=0)
