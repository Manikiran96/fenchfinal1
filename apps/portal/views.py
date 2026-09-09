"""
Mobile portals for Sales and Technician teams.

Design goals:
- Each team sees ONLY their own scope (their leads / their projects).
- Mobile-first templates (big touch targets, bottom nav).
- Admin gets a "today" monitoring view of sales activity.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.crm.models import Lead, LeadActivity, LeadStatus
from apps.projects.models import Project
from .models import StageUpdate, StagePhoto, WorkStage
from .forms import QuickLeadForm, FollowUpForm, StageUpdateForm


# ---------------------------------------------------------------------------
# Entry point — send each role to its own portal
# ---------------------------------------------------------------------------
@login_required
def portal_home(request):
    u = request.user
    if u.is_sales:
        return redirect("portal:sales_dashboard")
    if u.is_field_staff:
        return redirect("portal:tech_dashboard")
    # admins/others: default to the sales monitoring view
    return redirect("portal:sales_today_admin")


# ===========================================================================
# SALES PORTAL
# ===========================================================================
def _require_sales(user):
    if not (user.is_sales or user.is_admin_level or user.is_superuser):
        raise PermissionDenied("Sales portal is for the sales team.")


def _my_leads(user):
    """A sales exec sees their own leads; a manager/admin sees all."""
    qs = Lead.objects.select_related("assigned_to")
    if user.role == Role.SALES_EXECUTIVE:
        qs = qs.filter(assigned_to=user)
    return qs


@login_required
def sales_dashboard(request):
    _require_sales(request.user)
    today = timezone.localdate()
    leads = _my_leads(request.user)

    # follow-ups due today or overdue (not yet won/lost)
    due = (LeadActivity.objects
           .filter(lead__in=leads, next_follow_up__lte=today)
           .exclude(lead__status__in=[LeadStatus.WON, LeadStatus.LOST])
           .select_related("lead").order_by("next_follow_up"))

    stats = {
        "total": leads.count(),
        "today_created": leads.filter(created_at__date=today).count(),
        "won": leads.filter(status=LeadStatus.WON).count(),
        "open": leads.exclude(status__in=[LeadStatus.WON, LeadStatus.LOST]).count(),
        "due_count": due.count(),
    }
    return render(request, "portal/sales/dashboard.html", {
        "stats": stats, "due": due[:20], "recent": leads[:8],
    })


@login_required
def sales_lead_list(request):
    _require_sales(request.user)
    leads = _my_leads(request.user)
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    if q:
        leads = leads.filter(Q(customer_name__icontains=q) | Q(mobile__icontains=q))
    if status:
        leads = leads.filter(status=status)
    return render(request, "portal/sales/lead_list.html", {
        "leads": leads.distinct()[:100], "statuses": LeadStatus.choices,
        "q": q, "status": status,
    })


@login_required
def sales_lead_create(request):
    _require_sales(request.user)
    if request.method == "POST":
        form = QuickLeadForm(request.POST)
        if form.is_valid():
            lead = form.save(commit=False)
            lead.created_by = request.user
            lead.assigned_to = request.user
            lead.save()
            messages.success(request, f"Lead {lead.lead_number} created.")
            return redirect("portal:sales_lead_detail", pk=lead.pk)
    else:
        form = QuickLeadForm()
    return render(request, "portal/sales/lead_form.html", {"form": form})


@login_required
def sales_lead_detail(request, pk):
    _require_sales(request.user)
    lead = get_object_or_404(_my_leads(request.user), pk=pk)
    return render(request, "portal/sales/lead_detail.html", {
        "lead": lead, "followup_form": FollowUpForm(),
        "statuses": LeadStatus.choices,
    })


@login_required
def sales_add_followup(request, pk):
    _require_sales(request.user)
    lead = get_object_or_404(_my_leads(request.user), pk=pk)
    if request.method == "POST":
        # optional quick status change
        new_status = request.POST.get("status", "").strip()
        if new_status and new_status in dict(LeadStatus.choices):
            lead.status = new_status
            lead.save(update_fields=["status"])
        form = FollowUpForm(request.POST)
        if form.is_valid():
            act = form.save(commit=False)
            act.lead = lead
            act.created_by = request.user
            act.save()
            messages.success(request, "Follow-up saved.")
    return redirect("portal:sales_lead_detail", pk=lead.pk)


@login_required
def sales_today_admin(request):
    """Admin monitoring: what each sales person did TODAY."""
    if not (request.user.is_admin_level or request.user.is_superuser
            or request.user.role == Role.SALES_MANAGER):
        raise PermissionDenied("Admin/manager only.")
    today = timezone.localdate()

    reps = User.objects.filter(role__in=[Role.SALES_EXECUTIVE, Role.SALES_MANAGER])
    rows = []
    for rep in reps:
        created_today = Lead.objects.filter(assigned_to=rep, created_at__date=today).count()
        followups_today = LeadActivity.objects.filter(created_by=rep, created_at__date=today).count()
        open_leads = Lead.objects.filter(assigned_to=rep).exclude(
            status__in=[LeadStatus.WON, LeadStatus.LOST]).count()
        # "not following up" = open leads with NO activity in the last 3 days
        stale = 0
        for l in Lead.objects.filter(assigned_to=rep).exclude(
                status__in=[LeadStatus.WON, LeadStatus.LOST]):
            last = l.activities.order_by("-created_at").first()
            if (last is None) or ((today - last.created_at.date()).days > 3):
                stale += 1
        rows.append({
            "rep": rep, "created_today": created_today,
            "followups_today": followups_today, "open_leads": open_leads,
            "stale": stale, "active": followups_today > 0 or created_today > 0,
        })

    totals = {
        "created_today": sum(r["created_today"] for r in rows),
        "followups_today": sum(r["followups_today"] for r in rows),
        "stale": sum(r["stale"] for r in rows),
    }
    return render(request, "portal/sales/today_admin.html", {
        "rows": rows, "totals": totals, "today": today,
    })


# ===========================================================================
# TECHNICIAN PORTAL
# ===========================================================================
def _require_tech(user):
    if not (user.is_field_staff or user.is_admin_level or user.is_superuser):
        raise PermissionDenied("Technician portal is for field staff.")


def _my_projects(user):
    """Projects assigned to this technician (via Project.technicians M2M)."""
    qs = Project.objects.select_related("customer")
    if user.is_field_staff:
        qs = qs.filter(technicians=user)
    return qs.distinct()


@login_required
def tech_dashboard(request):
    _require_tech(request.user)
    projects = _my_projects(request.user)
    stats = {
        "total": projects.count(),
        "active": projects.exclude(stage__in=["COMMISSIONED", "CLOSED"]).count(),
        "updates_today": StageUpdate.objects.filter(
            technician=request.user, created_at__date=timezone.localdate()).count(),
    }
    return render(request, "portal/tech/dashboard.html", {
        "stats": stats, "projects": projects[:10],
    })


@login_required
def tech_project_list(request):
    _require_tech(request.user)
    projects = _my_projects(request.user)
    q = request.GET.get("q", "").strip()
    if q:
        projects = projects.filter(
            Q(project_number__icontains=q) | Q(customer__name__icontains=q) | Q(location__icontains=q))
    return render(request, "portal/tech/project_list.html", {"projects": projects[:100], "q": q})


@login_required
def tech_project_detail(request, pk):
    _require_tech(request.user)
    project = get_object_or_404(_my_projects(request.user), pk=pk)
    return render(request, "portal/tech/project_detail.html", {
        "project": project,
        "updates": project.stage_updates.select_related("technician").prefetch_related("photos"),
    })


@login_required
def tech_stage_update(request, pk):
    _require_tech(request.user)
    project = get_object_or_404(_my_projects(request.user), pk=pk)
    if request.method == "POST":
        form = StageUpdateForm(request.POST)
        if form.is_valid():
            update = form.save(commit=False)
            update.project = project
            update.technician = request.user
            update.created_by = request.user
            update.save()
            # save any attached photos (input name="photos", multiple)
            for f in request.FILES.getlist("photos"):
                StagePhoto.objects.create(stage_update=update, image=f, created_by=request.user)
            messages.success(request, "Update posted.")
            return redirect("portal:tech_project_detail", pk=project.pk)
    else:
        form = StageUpdateForm()
    return render(request, "portal/tech/stage_form.html", {
        "project": project, "form": form, "stages": WorkStage.choices,
    })
