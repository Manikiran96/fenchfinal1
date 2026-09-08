"""Quotation Management views (Module 3)."""
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from apps.accounts.permissions import role_required
from apps.accounts.models import Role
from apps.crm.models import Lead, LeadStatus
from .models import Quotation, QuotationStatus
from .forms import QuotationForm, QuotationItemFormSet, RejectForm, SendForm
from . import services

SALES_ROLES = (Role.SUPER_ADMIN, Role.ADMIN, Role.BRANCH_MANAGER, Role.SALES_MANAGER, Role.SALES_EXECUTIVE)


def _visible_quotations(user):
    qs = Quotation.objects.select_related("lead", "approved_by")
    if user.role == Role.SALES_EXECUTIVE:
        qs = qs.filter(lead__assigned_to=user)
    return qs


@role_required(*SALES_ROLES)
def quotation_list(request):
    return render(request, "quotations/quotation_list.html", {"quotations": _visible_quotations(request.user), "statuses": QuotationStatus.choices})


@role_required(*SALES_ROLES)
def quotation_rows(request):
    quotations = _visible_quotations(request.user)
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    if q:
        quotations = (quotations.filter(quotation_number__icontains=q) | quotations.filter(lead__customer_name__icontains=q))
    if status:
        quotations = quotations.filter(status=status)
    return render(request, "quotations/partials/quotation_rows.html", {"quotations": quotations.distinct()})


@role_required(*SALES_ROLES)
def quotation_create(request, lead_id):
    lead = get_object_or_404(Lead, pk=lead_id)
    quotation = Quotation(lead=lead)
    if request.method == "POST":
        form = QuotationForm(request.POST, instance=quotation)
        formset = QuotationItemFormSet(request.POST, instance=quotation)
        if form.is_valid():
            q = form.save(commit=False)
            q.created_by = request.user
            q.save()
            formset = QuotationItemFormSet(request.POST, instance=q)
            if formset.is_valid():
                formset.save()
            q.recalculate()
            if lead.status in (LeadStatus.NEW, LeadStatus.CONTACTED, LeadStatus.QUALIFIED, LeadStatus.SITE_VISIT):
                lead.status = LeadStatus.QUOTATION_SENT
                lead.save(update_fields=["status"])
            messages.success(request, f"Quotation {q.quotation_number} created.")
            return redirect("quotations:quotation_detail", pk=q.pk)
    else:
        form = QuotationForm(instance=quotation)
        formset = QuotationItemFormSet(instance=quotation)
    return render(request, "quotations/quotation_form.html", {"form": form, "formset": formset, "lead": lead, "title": "New Quotation"})


@role_required(*SALES_ROLES)
def quotation_edit(request, pk):
    q = get_object_or_404(_visible_quotations(request.user), pk=pk)
    if not q.is_editable:
        messages.error(request, "Only Draft or Rejected quotations can be edited.")
        return redirect("quotations:quotation_detail", pk=q.pk)
    if request.method == "POST":
        form = QuotationForm(request.POST, instance=q)
        formset = QuotationItemFormSet(request.POST, instance=q)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            q.recalculate()
            messages.success(request, "Quotation updated.")
            return redirect("quotations:quotation_detail", pk=q.pk)
    else:
        form = QuotationForm(instance=q)
        formset = QuotationItemFormSet(instance=q)
    return render(request, "quotations/quotation_form.html", {"form": form, "formset": formset, "lead": q.lead, "title": f"Edit {q.quotation_number}"})


@role_required(*SALES_ROLES)
def quotation_detail(request, pk):
    q = get_object_or_404(_visible_quotations(request.user), pk=pk)
    return render(request, "quotations/quotation_detail.html", {"q": q, "reject_form": RejectForm(), "send_form": SendForm(initial={"to_email": q.lead.email})})


@role_required(*SALES_ROLES)
def quotation_submit(request, pk):
    q = get_object_or_404(_visible_quotations(request.user), pk=pk)
    if q.status == QuotationStatus.DRAFT:
        q.submit_for_approval()
        messages.success(request, "Submitted for approval.")
    return redirect("quotations:quotation_detail", pk=q.pk)


@role_required(Role.SUPER_ADMIN, Role.ADMIN, Role.BRANCH_MANAGER, Role.SALES_MANAGER)
def quotation_approve(request, pk):
    q = get_object_or_404(Quotation, pk=pk)
    if q.status == QuotationStatus.PENDING_APPROVAL:
        q.approve(request.user)
        messages.success(request, f"Quotation {q.quotation_number} approved.")
    return redirect("quotations:quotation_detail", pk=q.pk)


@role_required(Role.SUPER_ADMIN, Role.ADMIN, Role.BRANCH_MANAGER, Role.SALES_MANAGER)
def quotation_reject(request, pk):
    q = get_object_or_404(Quotation, pk=pk)
    if q.status == QuotationStatus.PENDING_APPROVAL and request.method == "POST":
        form = RejectForm(request.POST)
        reason = form.cleaned_data.get("reason", "") if form.is_valid() else ""
        q.reject(request.user, reason)
        messages.info(request, "Quotation rejected.")
    return redirect("quotations:quotation_detail", pk=q.pk)


@role_required(*SALES_ROLES)
def quotation_revise(request, pk):
    q = get_object_or_404(_visible_quotations(request.user), pk=pk)
    clone = services.create_revision(q, request.user)
    messages.success(request, f"Created revision {clone.quotation_number} (rev {clone.revision}).")
    return redirect("quotations:quotation_edit", pk=clone.pk)


@role_required(*SALES_ROLES)
def quotation_pdf(request, pk):
    q = get_object_or_404(_visible_quotations(request.user), pk=pk)
    pdf = services.render_quotation_pdf(q)
    if pdf is None:
        return redirect("quotations:quotation_print", pk=q.pk)
    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{q.quotation_number}.pdf"'
    return resp


@role_required(*SALES_ROLES)
def quotation_print(request, pk):
    q = get_object_or_404(_visible_quotations(request.user), pk=pk)
    return render(request, "quotations/pdf.html", {"q": q, "items": q.items.all(), "company": settings.COMPANY, "print_mode": True})


@role_required(*SALES_ROLES)
def quotation_send(request, pk):
    q = get_object_or_404(_visible_quotations(request.user), pk=pk)
    if not q.can_send:
        messages.error(request, "Only approved quotations can be sent.")
        return redirect("quotations:quotation_detail", pk=q.pk)
    if request.method == "POST":
        form = SendForm(request.POST)
        if form.is_valid():
            services.email_quotation(q, to_email=form.cleaned_data["to_email"], extra_message=form.cleaned_data.get("message", ""))
            messages.success(request, f"Quotation emailed to {form.cleaned_data['to_email']}.")
    return redirect("quotations:quotation_detail", pk=q.pk)
