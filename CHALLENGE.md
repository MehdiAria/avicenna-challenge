# Take-Home: Notification Lifecycle

## What this is

A small, focused exercise. We care far more about the **decisions you make and why** than about how much code you write. Plan for **~2–3 hours**.

> Use whatever tools you like, including AI assistants. But everything you submit, you own: be ready to justify every decision live.

## The domain

A **Notification** is a single logical message to one user, to be delivered at `deliver_at`. A notification can be delivered over **Email**, **SMS**, or **both**.

The two channels are *not* the same. Their lifecycles differ:

| Channel | States seen in the wild              |
| ------- | ------------------------------------ |
| Email   | `sent`, `delivered`, `opened`, `bounced` |
| SMS     | `sent`, `delivered`, `failed`, `undelivered` |

**Sending is out of scope.** Two stubs are provided in `notification/providers.py`; assume they've already run for the sample notifications:

```python
def send_email(to: str, title: str, body: str) -> str: ...
def send_sms(to: str, text: str) -> str: ...
```

Each returns an opaque tracking id. The provider's later state reports reference that id.

## Task 1 — Model the channels

Extend `notification/models.py`. The starter `Notification` has a `user` and a `deliver_at`. Make it so a notification can carry an **Email and/or an SMS**, each with its own fields and its own current lifecycle state.

## Task 2 — Ingest state reports

Providers report lifecycle changes as **state reports** (`samples/state_reports.json`), delivered to `POST /api/notifications/`. Implement that endpoint.

These reports come off a network, from sources we don't completely trust. Assume thousands of reports per second at peak.

## Task 3 — Read endpoint

`GET /api/notifications/` returns the list of notifications, each with a **single status** that sensibly summarises the notification across **all** of its channels.

## Task 4 — Containerize

Containerize the application. It must use **PostgreSQL** (not SQLite). The app must **not accept HTTP traffic** until the database is fully migrated.

## What to hand back

- Your code, committed to git **incrementally** — commit as you go, one logical step at a time, rather than a single squashed drop. We read the history.
- It should run end to end: migrate, load `samples/`, hit the endpoint.
- A short note (a few paragraphs — in the README or a `NOTES.md`) covering:
  1. how you modeled the channels, and why;
  2. how you handle validation and handling of state reports, and why;
  3. your status-aggregation rule for multi-channel notifications, and why;
  4. how your implementation handles high load, and what you'd change at scale.
