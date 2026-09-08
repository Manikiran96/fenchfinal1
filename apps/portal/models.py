from django.conf import settings
from django.db import models
from apps.core.models import TimeStampedModel


class WorkStage(models.TextChoices):
    """Field-friendly work stages the technician updates on site."""
    SITE_SURVEY = "SITE_SURVEY", "Site Survey"
    STRUCTURE = "STRUCTURE", "Structure / Poles Fixing"
    PANEL_MOUNTING = "PANEL_MOUNTING", "Panel Mounting"
    WIRING = "WIRING", "Wiring & Cabling"
    INVERTER = "INVERTER", "Inverter Installation"
    METER = "METER", "Meter Fixing"
    TESTING = "TESTING", "Testing & Commissioning"
    HANDOVER = "HANDOVER", "Handover"


class StageUpdate(TimeStampedModel):
    """A single on-site progress update posted by a technician for a project.

    e.g. "Poles fixing done" with a note + photos. Multiple updates build a
    timeline of what happened on the project, day by day.
    """
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="stage_updates"
    )
    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="stage_updates"
    )
    stage = models.CharField(max_length=20, choices=WorkStage.choices)
    note = models.TextField(blank=True)
    is_done = models.BooleanField(default=False, help_text="Mark this stage as completed.")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_stage_display()} - {self.project.project_number}"


class StagePhoto(TimeStampedModel):
    """A photo attached to a stage update (before/after site photos)."""
    stage_update = models.ForeignKey(
        StageUpdate, on_delete=models.CASCADE, related_name="photos"
    )
    image = models.ImageField(upload_to="portal/stage_photos/")
    caption = models.CharField(max_length=120, blank=True)

    def __str__(self):
        return f"Photo for {self.stage_update_id}"
