import json
import uuid
from pathlib import Path


def demo_id(key):
    return uuid.uuid5(uuid.NAMESPACE_URL, "eventconnect:demo:" + key)


DEMO_EVENT_ID = demo_id("event.current")
FIXTURES = json.loads((Path(__file__).with_name("fixtures.json")).read_text(encoding="utf-8"))
