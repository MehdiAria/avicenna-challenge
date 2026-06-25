from datetime import datetime
from typing import Optional

from ninja import Router, Schema

from notification.models import EmailChannel, Notification, SMSChannel

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


# Higher = better outcome. Highest wins when aggregating across channels.
_STATUS_PRIORITY = {
    "opened": 5,
    "delivered": 4,
    "sent": 3,
    "undelivered": 2,
    "failed": 2,
    "bounced": 2,
}


def _aggregate_status(statuses: list[str]) -> str:
    if not statuses:
        return "pending"
    return max(statuses, key=lambda s: _STATUS_PRIORITY.get(s, 0))


class ChannelOut(Schema):
    tracking_id: str
    status: str


class NotificationOut(Schema):
    id: int
    user_id: int
    deliver_at: datetime
    status: str
    email: Optional[ChannelOut] = None
    sms: Optional[ChannelOut] = None


@router.get("/", response=list[NotificationOut])
def list_notifications(request):
    results = []
    qs = Notification.objects.prefetch_related("email", "sms").order_by("deliver_at")
    for notif in qs:
        channel_statuses = []
        email_out = None
        sms_out = None

        if hasattr(notif, "email"):
            channel_statuses.append(notif.email.status)
            email_out = ChannelOut(tracking_id=notif.email.tracking_id, status=notif.email.status)

        if hasattr(notif, "sms"):
            channel_statuses.append(notif.sms.status)
            sms_out = ChannelOut(tracking_id=notif.sms.tracking_id, status=notif.sms.status)

        results.append(
            NotificationOut(
                id=notif.pk,
                user_id=notif.user_id,
                deliver_at=notif.deliver_at,
                status=_aggregate_status(channel_statuses),
                email=email_out,
                sms=sms_out,
            )
        )
    return results
