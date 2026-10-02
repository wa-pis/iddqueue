"""Last-attempt diagnostics stored with the existing message JSONB."""

from datetime import datetime, timezone

from dramatiq.middleware import Middleware


class FailureMetadata(Middleware):
    def after_process_message(self, broker, message, *, result=None, exception=None):
        if exception is None:
            message.options.pop("pg_failure", None)
            return
        message.options["pg_failure"] = {
            "type": type(exception).__name__,
            "text": str(exception)[:2000],
            "time": datetime.now(timezone.utc).isoformat(),
            "attempt": message.options.get("retries", 0) + 1,
        }
