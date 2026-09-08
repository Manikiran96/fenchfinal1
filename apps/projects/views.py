"""Project Management views (Module 5)."""
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from apps.accounts.permissions import role_required
from apps.accounts.models import Role
from apps.quotations.models import Quotation
from .models import Project, ProjectStage
from .forms import ProjectCreateForm, ProjectUpdateForm, MilestoneForm, PaymentForm
from . import services

PROJECT_ROLES = (Role.SUPER_ADMIN, Role.ADMIN, Role.BRANCH_MANAGER, Role.PROJECT_MANAGER, Role.ACCOUNTS)
PROJECT_WRITE_ROLES = (Role.SUPER_ADMIN, Role.ADMIN, Role.BRANCH_MANAGER, Role.PROJECT_MANAGER)


def _visible_projects(user):
    qs = Project.objects.select_related("customer", "project_manager", "quotation")
    if user.role == Role.PROJECT_MANAGER:
        qs = qs.filter(project_manager=user)
    return qs


@role_required(*PROJECT_ROLES)
def project_list(request):
    return render(request, "projects/project_list.html", {"projects": _visible_projects(request.user), "stages": ProjectStage.choices})


@role_required(*PROJECT_ROLES)
def project_rows(request):
    projects = _visible_projects(request.user)
    q = request.GET.get("q", "").strip()
    stage = request.GET.get("stage", "").strip()
    if q:
        projects = projects.filter(Q(project_number__icontains=q) | Q(customer__name__icontains=q) | Q(location__icontains=q))
    if stage:
        projects = projects.filter(stage=stage)
    return render(request, "projects/partials/project_rows.html", {"projects": projects.distinct()})


@role_required(*PROJECT_WRITE_ROLES)
def project_create(request):
    initial = {}
    quotation = None
    qid = request.GET.get("quotation")
    if qid:
        quotation = Quotation.objects.filter(pk=qid).first()
        if quotation:
            initial = services.build_initial_from_quotation(quotation)
            initial["quotation"] = quotation.pk
            if getattr(quotation.lead, "customer", None):
                initial["customer"] = quotation.lead.customer.pk
    if request.method == "POST":
        form = ProjectCreateForm(request.POST)
        if form.is_valid():
            try:
                cd = form.cleaned_data
                project = services.create_project(customer=cd["customer"], advance_amount=cd["advance_amount"], project_value=cd["project_value"],
                    user=request.user, quotation=cd.get("quotation"), project_type=cd["project_type"], category=cd["category"], capacity_kw=cd["capacity_kw"],
                    subsidy_amount=cd["subsidy_amount"], location=cd.get("location", ""), latitude=cd.get("latitude"), longitude=cd.get("longitude"),
                    project_manager=cd.get("project_manager"), expected_completion=cd.get("expected_completion"))
                messages.success(request, f"Project {project.project_number} created.")
                return redirect("projects:project_detail", pk=project.pk)
            except services.AdvancePaymentRequired as exc:
                form.add_error("advance_amount", exc.message if hasattr(exc, "message") else str(exc))
    else:
        form = ProjectCreateForm(initial=initial)
    return render(request, "projects/project_form.html", {"form": form, "title": "New Project", "quotation": quotation, "is_create": True})


@role_required(*PROJECT_ROLES)
def project_detail(request, pk):
    project = get_object_or_404(_visible_projects(request.user), pk=pk)
    return render(request, "projects/project_detail.html", {"project": project, "milestone_form": MilestoneForm(),
        "payment_form": PaymentForm(initial={"paid_on": timezone.now().date()}), "can_write": request.user.can_manage_projects})


@role_required(*PROJECT_WRITE_ROLES)
def project_edit(request, pk):
    project = get_object_or_404(_visible_projects(request.user), pk=pk)
    form = ProjectUpdateForm(request.POST or None, instance=project)
    if request.method == "POST" and form.is_valid():
        proj = form.save(commit=False)
        if proj.stage == ProjectStage.COMMISSIONED and not proj.commissioned_on:
            proj.commissioned_on = timezone.now().date()
        proj.save()
        messages.success(request, "Project updated.")
        return redirect("projects:project_detail", pk=project.pk)
    return render(request, "projects/project_form.html", {"form": form, "title": f"Edit {project.project_number}", "is_create": False})


@role_required(*PROJECT_WRITE_ROLES)
def add_milestone(request, pk):
    project = get_object_or_404(_visible_projects(request.user), pk=pk)
    form = MilestoneForm(request.POST)
    if form.is_valid():
        m = form.save(commit=False)
        m.project = project
        m.created_by = request.user
        if m.is_done and not m.done_on:
            m.done_on = timezone.now().date()
        m.save()
    html = render_to_string("projects/partials/milestones.html", {"project": project}, request=request)
    return HttpResponse(html)


@role_required(*PROJECT_ROLES)
def add_payment(request, pk):
    project = get_object_or_404(_visible_projects(request.user), pk=pk)
    form = PaymentForm(request.POST)
    if form.is_valid():
        p = form.save(commit=False)
        p.project = project
        p.created_by = request.user
        p.save()
    project.refresh_from_db()
    html = render_to_string("projects/partials/finance.html", {"project": project}, request=request)
    return HttpResponse(html)
