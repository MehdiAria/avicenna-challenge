from django.db import models


class Notification(models.Model):
    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    deliver_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification #{self.pk} for {self.user_id}"


class EmailChannel(models.Model):
    class Status(models.TextChoices):
        SENT = "sent"
        DELIVERED = "delivered"
        OPENED = "opened"
        BOUNCED = "bounced"

    notification = models.OneToOneField(
        Notification,
        on_delete=models.CASCADE,
        related_name="email",
    )
    tracking_id = models.CharField(max_length=64, unique=True, db_index=True)
    to = models.EmailField()
    title = models.CharField(max_length=255)
    body = models.TextField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SENT)
    # tracks the occurred_at of the event that last set status (for out-of-order dedup)
    status_occurred_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Email({self.tracking_id}) → {self.to} [{self.status}]"


class SMSChannel(models.Model):
    class Status(models.TextChoices):
        SENT = "sent"
        DELIVERED = "delivered"
        FAILED = "failed"
        UNDELIVERED = "undelivered"

    notification = models.OneToOneField(
        Notification,
        on_delete=models.CASCADE,
        related_name="sms",
    )
    tracking_id = models.CharField(max_length=64, unique=True, db_index=True)
    to = models.CharField(max_length=32)
    text = models.TextField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SENT)
    status_occurred_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"SMS({self.tracking_id}) → {self.to} [{self.status}]"
