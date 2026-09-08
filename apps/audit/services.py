"""
Audit engine — reusable change tracking for any model.

Two ways to use it:

1) Automatic (recommended) — make a model inherit `AuditableModel` and set
   `AUDIT_MODULE = "projects"`. Every create/update is logged with a
   field-level diff. To capture WHO did it, set `instance._audit_user` in the
   view before saving (a tiny one-liner shown in the wiring notes).

2) Manual — call `log_change(...)` / `log_delete(...)` yourself from a view
   (useful for deletes or bulk actions).
"""
from django.forms.models import model_to_dict
from .models import AuditLog, AuditAction

# Fields we never want to diff/store (noise / sensitive).
_IGNORED = {"created_at", "updated_at", "password", "last_login"}


def _clean(value):
    """Make a value JSON-serializable + readable for the audit record."""
    if value is None:
        return None
    # FK ids, decimals, dates -> str; keep it simple and human-readable.
    return str(value)


def _snapshot(instance):
    """Dict of field -> value for the model (excludes ignored/M2M)."""
    data = {}
    for field in instance._meta.concrete_fields:
        if field.name in _IGNORED:
            continue
        data[field.name] = _clean(getattr(instance, field.attname, None))
    return data


def diff(old, new):
    """Return list of {field, old, new} for fields that changed."""
    changes = []
    keys = set(old) | set(new)
    for k in sorted(keys):
        o, n = old.get(k), new.get(k)
        if o != n:
            changes.append({"field": k, "old": o, "new": n})
    return changes


def _user_label(user):
    if not user:
        return "System"
    return user.get_full_name() or getattr(user, "username", "") or str(user)


def write(*, module, instance, action, changes=None, user=None):
    """Create an AuditLog row."""
    return AuditLog.objects.create(
        module=module,
        object_repr=str(instance)[:200],
        model_name=instance.__class__.__name__,
        object_id=str(getattr(instance, "pk", "") or ""),
        action=action,
        changes=changes or [],
        user=user if getattr(user, "pk", None) else None,
        user_label=_user_label(user),
    )


def log_change(*, module, instance, old_snapshot, user=None):
    """Log an UPDATE by diffing an old snapshot against the current instance."""
    changes = diff(old_snapshot, _snapshot(instance))
    if not changes:
        return None
    return write(module=module, instance=instance, action=AuditAction.UPDATE,
                 changes=changes, user=user)


def log_create(*, module, instance, user=None):
    return write(module=module, instance=instance, action=AuditAction.CREATE, user=user)


def log_delete(*, module, instance, user=None):
    return write(module=module, instance=instance, action=AuditAction.DELETE, user=user)


def snapshot(instance):
    """Public helper so views can grab a 'before' snapshot for manual logging."""
    return _snapshot(instance)
