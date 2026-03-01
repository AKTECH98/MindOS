import re

# Google Calendar recurring event instances have an ID like "<baseId>_20260301T140000Z".
# We always store/query by the base event ID so sessions/completions accumulate correctly across days.
_RECURRENCE_SUFFIX = re.compile(r"_\d{8}T\d{6}Z?$")

def base_event_id(event_id: str) -> str:
    """Strip Google Calendar recurrence instance suffix, returning the base event ID."""
    return _RECURRENCE_SUFFIX.sub("", event_id)
