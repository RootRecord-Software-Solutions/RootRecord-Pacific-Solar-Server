#!/usr/bin/env python3
"""The closer speaks only after all ten desks land in one cycle."""
import os
from datetime import datetime
from zoneinfo import ZoneInfo

os.environ["RR_VOICE_STATUS"] = "0"
os.environ["RR_VOICE_STACK_STATE"] = "/tmp/rr-stack-send-test.json"

import status_cue

HST = ZoneInfo("Pacific/Honolulu")
WHEN = datetime(2026, 10, 2, 12, 20, tzinfo=HST)


def test_cycle_crosses_the_hour():
    assert status_cue.cycle_key(datetime(2026, 10, 2, 12, 18, tzinfo=HST)) == "2026-10-02T12:12"
    assert status_cue.cycle_key(datetime(2026, 10, 2, 0, 4, tzinfo=HST)) == "2026-10-01T23:42"


def test_closer_waits_for_every_desk():
    try:
        os.unlink("/tmp/rr-stack-send-test.json")
    except OSError:
        pass
    names = list(status_cue.TYPES)
    last = None
    for name in names[:-1]:
        assert status_cue.note_sent(name, WHEN) is None
    last = status_cue.note_sent(names[-1], WHEN)
    assert last and last.get("ok") and last.get("phase") == "stack_all_sent"
    assert status_cue.note_sent(names[-1], WHEN) is None


if __name__ == "__main__":
    test_cycle_crosses_the_hour()
    test_closer_waits_for_every_desk()
    print("ok")
