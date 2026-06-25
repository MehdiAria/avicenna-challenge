import json
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from notification.models import EmailChannel, Notification, SMSChannel

SAMPLES_DIR = Path(__file__).resolve().parents[3] / "samples"

# tracking IDs that match state_reports.json
TRACKING_IDS = {
    1: {"email": "em_a1f0c97d2b3e", "sms": "sm_77b3e0148aa2"},
    2: {"email": "em_5c2d81f4a019"},
    3: {"sms": "sm_0e9a4f6c7d55"},
}


class Command(BaseCommand):
    help = "Load sample notifications and state reports from samples/"

    def handle(self, *args, **options):
        notifications_data = json.loads((SAMPLES_DIR / "notifications.json").read_text())
        state_reports = json.loads((SAMPLES_DIR / "state_reports.json").read_text())

        for entry in notifications_data:
            user, _ = User.objects.get_or_create(username=entry["user"])
            notif, created = Notification.objects.get_or_create(
                id=entry["id"],
                defaults={"user": user, "deliver_at": entry["deliver_at"]},
            )

            tracking = TRACKING_IDS.get(entry["id"], {})
            channels = entry.get("channels", {})

            if "email" in channels and "email" in tracking:
                EmailChannel.objects.get_or_create(
                    notification=notif,
                    defaults={
                        "tracking_id": tracking["email"],
                        "to": channels["email"]["to"],
                        "title": channels["email"]["title"],
                        "body": channels["email"]["body"],
                    },
                )

            if "sms" in channels and "sms" in tracking:
                SMSChannel.objects.get_or_create(
                    notification=notif,
                    defaults={
                        "tracking_id": tracking["sms"],
                        "to": channels["sms"]["to"],
                        "text": channels["sms"]["text"],
                    },
                )

            if created:
                self.stdout.write(f"  created notification {notif.id} for {entry['user']}")

        self.stdout.write(self.style.SUCCESS(f"loaded {len(notifications_data)} notifications"))

        from datetime import datetime, timezone

        updated = skipped = 0
        for report in state_reports:
            tid = report["tracking_id"]
            occurred_at = datetime.fromisoformat(report["occurred_at"].replace("Z", "+00:00"))

            if tid.startswith("em_"):
                qs = EmailChannel.objects.filter(tracking_id=tid)
                valid = {c.value for c in EmailChannel.Status}
            elif tid.startswith("sm_"):
                qs = SMSChannel.objects.filter(tracking_id=tid)
                valid = {c.value for c in SMSChannel.Status}
            else:
                skipped += 1
                continue

            channel = qs.first()
            if not channel or report["status"] not in valid:
                skipped += 1
                continue

            if channel.status_occurred_at is None or occurred_at > channel.status_occurred_at:
                channel.status = report["status"]
                channel.status_occurred_at = occurred_at
                channel.save(update_fields=["status", "status_occurred_at"])
                updated += 1
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(f"processed state reports: {updated} applied, {skipped} skipped")
        )