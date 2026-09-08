from django.conf import settings
from django.db import models


class AuditAction(models.TextChoices):
    CREATE = "CREATE", "Created"
    UPDATE = "UPDATE", "Updated"
    DELETE = "DELETE", "Deleted"


class AuditLog(models.Model):
    """A single audit record: WHO changed WHAT, WHEN, in which MODULE.

    For UPDATE actions we store field-level diffs in `changes`, e.g.:
        [{"field": "name", "old": "Old Project", "new": "New Project"}]
    so you can see exactly what value changed from what to what.
    """
    # Module category, e.g. "projects", "finance", "inventory".
    module = models.CharField(max_length=40, db_index=True)
    # Human label of the record, e.g. "PRJ20260001".
    object_repr = models.CharField(max_length=200)
    # Model name, e.g. "Project", "Customer".
    model_name = models.CharField(max_length=60)
    object_id = models.CharField(max_length=40, blank=True)

    action = models.CharField(max_length=10, choices=AuditAction.choices, db_index=True)
    # Field-level changes (list of {field, old, new}); empty for create/delete.
    changes = models.JSONField(default=list, blank=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="audit_logs",
    )
    user_label = models.CharField(max_length=150, blank=True)  # cached name even if user deleted
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["module", "-created_at"])]

    def __str__(self):
        return f"{self.get_action_display()} {self.model_name} {self.object_repr}"
