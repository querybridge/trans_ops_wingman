from django.conf import settings
from django.db import models

SEVERITIES = [("critical", "Critical"), ("warning", "Warning")]


def default_severities():
    return ["critical"]


class UserPreference(models.Model):
    """Per-user defaults. An empty region list means all regions."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="preference")
    worklist_regions = models.JSONField(default=list, blank=True)
    worklist_severities = models.JSONField(default=default_severities)

    def __str__(self):
        return f"Preferences for {self.user}"

    @classmethod
    def for_user(cls, user):
        """The saved preference, or unsaved defaults if the user has never changed them."""
        return cls.objects.filter(user=user).first() or cls(user=user)
