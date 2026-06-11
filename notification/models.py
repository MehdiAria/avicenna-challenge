from django.db import models


class Notification(models.Model):
    """A single logical message to one user (see CHALLENGE.md, Task 1)."""

    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    deliver_at = models.DateTimeField(
        help_text="When this notification should be delivered"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification #{self.pk} for {self.user_id}"
