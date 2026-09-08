"""
Finance views (Module 8).

- Dashboard: consolidated receivables / payables / revenue / subsidy.
- Receivables: project balances + AMC balances (record AMC payments).
- Payables: outstanding purchase orders (record supplier payments).
- Expenses, Subsidy claims, and Net-metering tracking.
"""
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.permissions import role_required
from apps.accounts.models import Role
from apps.projects.models import Project
from apps.inventory.models import PurchaseOrder, POStatus
from apps.service.models import AMCContract
from .models import Expense, SubsidyClaim, NetMetering
from .forms import (SupplierPaymentForm, AMCPaymentForm, ExpenseForm, SubsidyClaimForm, NetMeteringForm)
from . import services

# Finance is visible to management + accounts + subsidy coordinator.
FINANCE_VIEW_ROLES = (Role.SUPER_ADMIN, Role.ADMIN, Role.BRANCH_MANAGER, Role.ACCOUNTS, Role.SUBSIDY_COORDINATOR)
FINANCE_WRITE_ROLES = (Role.SUPER_ADMIN, Role.ADMIN, Role.BRANCH_MANAGER, Role.ACCOUNTS, Role.SUBSIDY_COORDINATOR)


@role_required(*FINANCE_VIEW_ROLES)
def dashboard(request):
    ctx = services.dashboard_context()
    return render(request, "finance/dashboard.html", ctx)


# --------------------------- Receivables ---------------------------
@role_required(*FINANCE_VIEW_ROLES)
def receivables(request):
    projects = Project.objects.select_related("customer").all()
    projects_due = [p for p in projects if p.pending_amount and p.pending_amount > 0]
    amcs = AMCContract.objects.select_related("customer").all()
    amcs_due = [a for a in amcs if a.amc_balance and a.amc_balance > 0]
    return render(request, "finance/receivables.html", {
        "projects_due": projects_due, "amcs_due": amcs_due,
        "amc_pay_form": AMCPaymentForm(),
        "summary": services.receivables_summary()})


@role_required(*FINANCE_WRITE_ROLES)
def pay_amc(request, amc_id):
    amc = get_object_or_404(AMCContract, pk=amc_id)
    if request.method == "POST":
        form = AMCPaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.amc = amc
            payment.created_by = request.user
            payment.save()  # AMCPayment.save() updates amc.amount_paid
            messages.success(request, f"Recorded Rs {payment.amount} against {amc.contract_number}.")
    return redirect("finance:receivables")


# --------------------------- Payables ---------------------------
@role_required(*FINANCE_VIEW_ROLES)
def payables(request):
    orders = (PurchaseOrder.objects.select_related("supplier", "warehouse")
              .exclude(status=POStatus.DRAFT).exclude(status=POStatus.CANCELLED))
    orders_due = [po for po in orders if po.payable_balance and po.payable_balance > 0]
    return render(request, "finance/payables.html", {
        "orders_due": orders_due, "pay_form": SupplierPaymentForm(),
        "summary": services.payables_summary()})


@role_required(*FINANCE_WRITE_ROLES)
def pay_supplier(request, po_id):
    po = get_object_or_404(PurchaseOrder, pk=po_id)
    if request.method == "POST":
        form = SupplierPaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.purchase_order = po
            payment.created_by = request.user
            payment.save()  # SupplierPayment.save() updates po.amount_paid
            messages.success(request, f"Recorded Rs {payment.amount} to {po.supplier.name}.")
    return redirect("finance:payables")


# --------------------------- Expenses ---------------------------
@role_required(*FINANCE_VIEW_ROLES)
def expense_list(request):
    expenses = Expense.objects.select_related("project").all()
    q = request.GET.get("q", "").strip()
    if q:
        expenses = expenses.filter(Q(expense_number__icontains=q) | Q(description__icontains=q))
    total = sum((e.amount for e in expenses), 0)
    return render(request, "finance/expense_list.html", {"expenses": expenses, "total": total})


@role_required(*FINANCE_WRITE_ROLES)
def expense_create(request):
    form = ExpenseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        exp = form.save(commit=False)
        exp.created_by = request.user
        exp.save()
        messages.success(request, f"Expense {exp.expense_number} recorded.")
        return redirect("finance:expense_list")
    return render(request, "finance/simple_form.html", {"form": form, "title": "Record Expense", "back": "finance:expense_list"})


# --------------------------- Subsidy ---------------------------
@role_required(*FINANCE_VIEW_ROLES)
def subsidy_list(request):
    claims = SubsidyClaim.objects.select_related("project", "project__customer").all()
    return render(request, "finance/subsidy_list.html", {"claims": claims, "summary": services.subsidy_summary()})


@role_required(*FINANCE_WRITE_ROLES)
def subsidy_create(request):
    form = SubsidyClaimForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        claim = form.save(commit=False)
        claim.created_by = request.user
        if not claim.coordinator:
            claim.coordinator = request.user
        claim.save()
        messages.success(request, f"Subsidy claim {claim.claim_number} created.")
        return redirect("finance:subsidy_list")
    return render(request, "finance/simple_form.html", {"form": form, "title": "New Subsidy Claim", "back": "finance:subsidy_list"})


@role_required(*FINANCE_WRITE_ROLES)
def subsidy_edit(request, pk):
    claim = get_object_or_404(SubsidyClaim, pk=pk)
    form = SubsidyClaimForm(request.POST or None, instance=claim)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Subsidy claim updated.")
        return redirect("finance:subsidy_list")
    return render(request, "finance/simple_form.html", {"form": form, "title": f"Edit {claim.claim_number}", "back": "finance:subsidy_list"})


# --------------------------- Net metering ---------------------------
@role_required(*FINANCE_VIEW_ROLES)
def netmetering_list(request):
    records = NetMetering.objects.select_related("project", "project__customer").all()
    return render(request, "finance/netmetering_list.html", {"records": records})


@role_required(*FINANCE_WRITE_ROLES)
def netmetering_create(request):
    form = NetMeteringForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        nm = form.save(commit=False)
        nm.created_by = request.user
        nm.save()
        messages.success(request, "Net-metering record created.")
        return redirect("finance:netmetering_list")
    return render(request, "finance/simple_form.html", {"form": form, "title": "New Net-Metering Record", "back": "finance:netmetering_list"})


@role_required(*FINANCE_WRITE_ROLES)
def netmetering_edit(request, pk):
    nm = get_object_or_404(NetMetering, pk=pk)
    form = NetMeteringForm(request.POST or None, instance=nm)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Net-metering record updated.")
        return redirect("finance:netmetering_list")
    return render(request, "finance/simple_form.html", {"form": form, "title": f"Edit Net-Metering ({nm.project.project_number})", "back": "finance:netmetering_list"})
