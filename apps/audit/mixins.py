"""
AuditableModel — inherit this to auto-log create/update with field diffs.

Usage:
    from apps.audit.mixins import AuditableModel

    class Project(AuditableModel, TimeStampedModel):
        AUDIT_MODULE = "projects"
        ...

To record WHO made the change, set `instance._audit_user = request.user`
in the view right before `.save()`. If not set, the change is logged as
"System" (still captures old->new values).
"""
from django.db import models
from . import services
from .models import AuditAction


class AuditableModel(models.Model):
    #: Module category shown/filterable in the audit log. Override per model.
    AUDIT_MODULE = "general"

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remember the state loaded from DB so we can diff on save.
        self._audit_loaded = services.snapshot(self) if self.pk else None

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        instance._audit_loaded = services.snapshot(instance)
        return instance

    def save(self, *args, **kwargs):
        is_create = self._state.adding
        user = getattr(self, "_audit_user", None)
        old = getattr(self, "_audit_loaded", None)

        super().save(*args, **kwargs)

        if is_create:
            services.log_create(module=self.AUDIT_MODULE, instance=self, user=user)
        else:
            # Diff previous snapshot vs current values.
            if old is not None:
                changes = services.diff(old, services.snapshot(self))
                if changes:
                    services.write(module=self.AUDIT_MODULE, instance=self,
                                   action=AuditAction.UPDATE, changes=changes, user=user)
        # Refresh baseline for any subsequent saves in the same request.
        self._audit_loaded = services.snapshot(self)

    def delete(self, *args, **kwargs):
        user = getattr(self, "_audit_user", None)
        services.log_delete(module=self.AUDIT_MODULE, instance=self, user=user)
        return super().delete(*args, **kwargs)
