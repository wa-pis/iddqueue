"""A separate domain using the same broker at startup."""
from iddqueue import Domain

notifications = Domain("notifications")


@notifications.actor(store_results=True)
def notify(text):
    return text
