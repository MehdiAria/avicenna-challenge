"""Outbound provider stubs (see CHALLENGE.md).

Each call "sends" a message and returns an opaque tracking id. Providers later
report lifecycle changes against that id (see ``samples/state_reports.json``).
"""

import uuid


def send_email(to: str, title: str, body: str) -> str:
    return "em_" + uuid.uuid4().hex[:12]


def send_sms(to: str, text: str) -> str:
    return "sm_" + uuid.uuid4().hex[:12]
