"""Service module views (Module 7): tickets, technicians, AMC."""
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string

from apps.accounts.permissions import role_required
from apps.accounts.models import Role
from .models import Technician, ServiceTicket, TicketStatus, TicketPriority, AMCContract
from .forms import (TechnicianForm, TicketForm, AssignForm, StatusForm, UpdateForm, AMCForm, VisitCompleteForm)
from . import services

SERVICE_VIEW_ROLES = (Role.SUPER_ADMIN, Role.ADMIN, Role.BRANCH_MANAGER, Role.SERVICE_ENGINEER, Role.PROJECT_MANAGER, Role.TECHNICIAN, Role.ACCOUNTS)
SERVICE_MANAGE_ROLES = (Role.SUPER_ADMIN, Role.ADMIN, Role.BRANCH_MANAGER, Role.SERVICE_ENGINEER, Role.PROJECT_MANAGER)


def _visible_tickets(user):
    qs = ServiceTicket.objects.select_related("customer", "project", "assigned_to__user")
    if user.role == Role.TECHNICIAN:
        qs = qs.filter(assigned_to__user=user)
    return qs


@role_required(*SERVICE_VIEW_ROLES)
def ticket_list(request):
    return render(request, "service/ticket_list.html", {"tickets": _visible_tickets(request.user),
        "statuses": TicketStatus.choices, "priorities": TicketPriority.choices})


@role_required(*SERVICE_VIEW_ROLES)
def ticket_rows(request):
    tickets = _visible_tickets(request.user)
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    priority = request.GET.get("priority", "").strip()
    if q:
        tickets = tickets.filter(Q(ticket_number__icontains=q) | Q(title__icontains=q) | Q(customer__name__icontains=q))
    if status:
        tickets = tickets.filter(status=status)
    if priority:
        tickets = tickets.filter(priority=priority)
    return render(request, "service/partials/ticket_rows.html", {"tickets": tickets.distinct()})


@role_required(*SERVICE_MANAGE_ROLES)
def ticket_create(request):
    if request.method == "POST":
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user
            ticket.save()
            messages.success(request, f"Ticket {ticket.ticket_number} created.")
            return redirect("service:ticket_detail", pk=ticket.pk)
    else:
        form = TicketForm()
    return render(request, "service/ticket_form.html", {"form": form, "title": "New Service Ticket"})


@role_required(*SERVICE_VIEW_ROLES)
def ticket_detail(request, pk):
    ticket = get_object_or_404(_visible_tickets(request.user), pk=pk)
    return render(request, "service/ticket_detail.html", {"ticket": ticket, "assign_form": AssignForm(),
        "status_form": StatusForm(initial={"new_status": ticket.status}), "update_form": UpdateForm(), "can_manage": request.user.can_manage_service})


@role_required(*SERVICE_MANAGE_ROLES)
def ticket_assign(request, pk):
    ticket = get_object_or_404(ServiceTicket, pk=pk)
    form = AssignForm(request.POST)
    if form.is_valid():
        services.assign_ticket(ticket, form.cleaned_data["technician"], user=request.user, note=form.cleaned_data.get("note", ""))
        messages.success(request, "Ticket assigned.")
    return redirect("service:ticket_detail", pk=ticket.pk)


@role_required(*SERVICE_VIEW_ROLES)
def ticket_status(request, pk):
    ticket = get_object_or_404(_visible_tickets(request.user), pk=pk)
    form = StatusForm(request.POST)
    if form.is_valid():
        services.change_status(ticket, form.cleaned_data["new_status"], user=request.user, resolution=form.cleaned_data.get("resolution", ""))
        messages.success(request, "Status updated.")
    return redirect("service:ticket_detail", pk=ticket.pk)


@role_required(*SERVICE_VIEW_ROLES)
def ticket_update(request, pk):
    ticket = get_object_or_404(_visible_tickets(request.user), pk=pk)
    form = UpdateForm(request.POST)
    if form.is_valid():
        services.add_update(ticket, form.cleaned_data["note"], user=request.user)
    html = render_to_string("service/partials/timeline.html", {"ticket": ticket}, request=request)
    return HttpResponse(html)


@role_required(*SERVICE_VIEW_ROLES)
def technician_list(request):
    return render(request, "service/technician_list.html", {"technicians": Technician.objects.select_related("user").all()})


@role_required(*SERVICE_MANAGE_ROLES)
def technician_create(request):
    form = TechnicianForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        tech = form.save(commit=False)
        tech.created_by = request.user
        tech.save()
        messages.success(request, f"Technician {tech.employee_code} added.")
        return redirect("service:technician_list")
    return render(request, "service/simple_form.html", {"form": form, "title": "New Technician", "back": "service:technician_list"})


@role_required(*SERVICE_VIEW_ROLES)
def amc_list(request):
    return render(request, "service/amc_list.html", {"contracts": AMCContract.objects.select_related("customer").all()})


@role_required(*SERVICE_MANAGE_ROLES)
def amc_create(request):
    if request.method == "POST":
        form = AMCForm(request.POST)
        if form.is_valid():
            amc = form.save(commit=False)
            amc.created_by = request.user
            amc.save()
            services.generate_amc_visits(amc, user=request.user)
            messages.success(request, f"AMC {amc.contract_number} created with scheduled visits.")
            return redirect("service:amc_detail", pk=amc.pk)
    else:
        form = AMCForm()
    return render(request, "service/amc_form.html", {"form": form, "title": "New AMC Contract"})


@role_required(*SERVICE_VIEW_ROLES)
def amc_detail(request, pk):
    amc = get_object_or_404(AMCContract.objects.select_related("customer", "project"), pk=pk)
    return render(request, "service/amc_detail.html", {"amc": amc, "visit_form": VisitCompleteForm(), "can_manage": request.user.can_manage_service})


@role_required(*SERVICE_MANAGE_ROLES)
def amc_generate_visits(request, pk):
    amc = get_object_or_404(AMCContract, pk=pk)
    created = services.generate_amc_visits(amc, user=request.user)
    messages.success(request, f"Generated {len(created)} visit(s).")
    return redirect("service:amc_detail", pk=amc.pk)


@role_required(*SERVICE_VIEW_ROLES)
def amc_complete_visit(request, visit_id):
    from .models import AMCVisit
    visit = get_object_or_404(AMCVisit, pk=visit_id)
    form = VisitCompleteForm(request.POST)
    if form.is_valid():
        services.complete_visit(visit, user=request.user, remarks=form.cleaned_data.get("remarks", ""), technician=form.cleaned_data.get("technician"))
        messages.success(request, "Visit marked complete.")
    return redirect("service:amc_detail", pk=visit.amc_id)
