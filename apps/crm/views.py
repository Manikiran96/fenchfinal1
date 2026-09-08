"""CRM / Leads views — HTMX partial pattern."""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.http import HttpResponse
from apps.accounts.permissions import role_required
from apps.accounts.models import Role
from .models import Lead, LeadStatus
from .forms import LeadForm, LeadActivityForm

SALES_ROLES = (Role.SUPER_ADMIN, Role.ADMIN, Role.BRANCH_MANAGER, Role.SALES_MANAGER, Role.SALES_EXECUTIVE)


def _visible_leads(user):
    qs = Lead.objects.select_related("assigned_to")
    if user.role == Role.SALES_EXECUTIVE:
        qs = qs.filter(assigned_to=user)
    return qs


@role_required(*SALES_ROLES)
def lead_list(request):
    return render(request, "crm/lead_list.html", {"leads": _visible_leads(request.user), "statuses": LeadStatus.choices})


@role_required(*SALES_ROLES)
def lead_rows(request):
    leads = _visible_leads(request.user)
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    if q:
        leads = leads.filter(customer_name__icontains=q) | leads.filter(mobile__icontains=q)
    if status:
        leads = leads.filter(status=status)
    return render(request, "crm/partials/lead_rows.html", {"leads": leads.distinct()})


@role_required(*SALES_ROLES)
def lead_create(request):
    if request.method == "POST":
        form = LeadForm(request.POST)
        if form.is_valid():
            lead = form.save(commit=False)
            lead.created_by = request.user
            if not lead.assigned_to:
                lead.assigned_to = request.user
            lead.save()
            messages.success(request, f"Lead {lead.lead_number} created.")
            if request.htmx:
                resp = HttpResponse()
                resp["HX-Redirect"] = redirect("crm:lead_detail", pk=lead.pk).url
                return resp
            return redirect("crm:lead_detail", pk=lead.pk)
    else:
        form = LeadForm()
    return render(request, "crm/lead_form.html", {"form": form, "title": "New Lead"})


@role_required(*SALES_ROLES)
def lead_edit(request, pk):
    lead = get_object_or_404(_visible_leads(request.user), pk=pk)
    form = LeadForm(request.POST or None, instance=lead)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Lead updated.")
        return redirect("crm:lead_detail", pk=lead.pk)
    return render(request, "crm/lead_form.html", {"form": form, "title": f"Edit {lead.lead_number}"})


@role_required(*SALES_ROLES)
def lead_detail(request, pk):
    lead = get_object_or_404(_visible_leads(request.user), pk=pk)
    return render(request, "crm/lead_detail.html", {"lead": lead, "activity_form": LeadActivityForm(), "quotations": lead.quotations.all()})


@role_required(*SALES_ROLES)
def add_activity(request, pk):
    lead = get_object_or_404(_visible_leads(request.user), pk=pk)
    form = LeadActivityForm(request.POST)
    if form.is_valid():
        activity = form.save(commit=False)
        activity.lead = lead
        activity.created_by = request.user
        activity.save()
    html = render_to_string("crm/partials/timeline.html", {"lead": lead}, request=request)
    return HttpResponse(html)
