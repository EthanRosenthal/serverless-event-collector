from pynamodb.models import DoesNotExist, Model

from collector.dynamo.button import ButtonClickCounter
from collector.dynamo.web import PageViewCounter


def update_count(CountModel: Model, *args) -> None:
    """Add 1 to the counts for a dynamodb model that tracks event counts"""
    if not CountModel.exists():
        CountModel.create_table(billing_mode="PAY_PER_REQUEST", wait=True)

    # Get the model from dyanmodb. If it doesn't exist yet, then create it.
    try:
        model = CountModel.get(*args)
    except DoesNotExist:
        model = CountModel(*args)
        model.save()

    # Add 1 to the model's count.
    model.update(actions=[CountModel.count.set(CountModel.count + 1)])  # type: ignore
