from datetime import datetime

from ninja import Router, Schema

from notification.models import EmailChannel, SMSChannel

router = Router()

EMAIL_STATUSES = {c.value for c in EmailChannel.Status}
SMS_STATUSES = {c.value for c in SMSChannel.Status}


class StateReport(Schema):
    tracking_id: str
    status: str
    occurred_at: datetime
    received_at: datetime


@router.post("/")
def ingest_state_reports(request, reports: list[StateReport]):
    updated = 0
    skipped = 0

    for report in reports:
        tid = report.tracking_id

        if tid.startswith("em_"):
            try:
                channel = EmailChannel.objects.get(tracking_id=tid)
            except EmailChannel.DoesNotExist:
                skipped += 1
                continue
            if report.status not in EMAIL_STATUSES:
                skipped += 1
                continue
        elif tid.startswith("sm_"):
            try:
                channel = SMSChannel.objects.get(tracking_id=tid)
            except SMSChannel.DoesNotExist:
                skipped += 1
                continue
            if report.status not in SMS_STATUSES:
                skipped += 1
                continue
        else:
            skipped += 1
            continue

        if channel.status_occurred_at is None or report.occurred_at > channel.status_occurred_at:
            channel.status = report.status
            channel.status_occurred_at = report.occurred_at
            channel.save(update_fields=["status", "status_occurred_at"])
            updated += 1
        else:
            skipped += 1

    return {"updated": updated, "skipped": skipped}


@router.get("/")
def list_notifications(request):
    """List notifications, each with a single status (see CHALLENGE.md, Task 3)."""
    return []
