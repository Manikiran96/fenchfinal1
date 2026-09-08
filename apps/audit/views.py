"""Audit log viewer — filter by module, action, and search."""
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import render

from .models import AuditLog, AuditAction


@login_required
def audit_list(request):
    # Only management/admins can view the audit trail.
    u = request.user
    if not (u.is_admin_level or u.is_superuser):
        raise PermissionDenied("Audit log is restricted to administrators.")

    logs = AuditLog.objects.select_related("user")
    module = request.GET.get("module", "").strip()
    action = request.GET.get("action", "").strip()
    q = request.GET.get("q", "").strip()

    if module:
        logs = logs.filter(module=module)
    if action:
        logs = logs.filter(action=action)
    if q:
        logs = logs.filter(
            Q(object_repr__icontains=q) | Q(user_label__icontains=q) | Q(model_name__icontains=q))

    # Distinct module list for the filter dropdown.
    modules = (AuditLog.objects.values_list("module", flat=True).distinct().order_by("module"))

    return render(request, "audit/audit_list.html", {
        "logs": logs[:300],
        "modules": modules,
        "actions": AuditAction.choices,
        "module": module, "action": action, "q": q,
    })
