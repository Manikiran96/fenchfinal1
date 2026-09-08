"""
Finance consolidation layer.

The single place that rolls up money from every module into one financial
picture — used by the dashboard and reports. Kept out of the view so the
same numbers can feed an API, a PDF, or a scheduled report later.
"""
from decimal import Decimal
from django.db.models import Sum, F, DecimalField
from django.db.models.functions import Coalesce

from apps.projects.models import Project
from apps.inventory.models import PurchaseOrder
from apps.service.models import AMCContract
from .models import Expense, SubsidyClaim, NetMetering, SubsidyStatus

ZERO = Decimal("0")
_D = DecimalField(max_digits=16, decimal_places=2)


def _sum(qs, field):
    return qs.aggregate(t=Coalesce(Sum(field), ZERO, output_field=_D))["t"] or ZERO


def receivables_summary():
    """Money owed TO us: outstanding project balances + AMC balances."""
    # Project receivables: sum of pending_amount across all projects.
    project_pending = _sum(Project.objects.all(), "pending_amount")

    # AMC receivables: contract amount - amount_paid (only where positive).
    amc_total = _sum(AMCContract.objects.all(), "amount")
    amc_paid = _sum(AMCContract.objects.all(), "amount_paid")
    amc_pending = max(amc_total - amc_paid, ZERO)

    return {
        "project_pending": project_pending,
        "amc_pending": amc_pending,
        "total": project_pending + amc_pending,
    }


def payables_summary():
    """Money WE owe: outstanding purchase-order balances (total - paid)."""
    # Only POs that have been ordered/received carry a real payable.
    active = PurchaseOrder.objects.exclude(status="DRAFT").exclude(status="CANCELLED")
    po_total = _sum(active, "total_amount")
    po_paid = _sum(active, "amount_paid")
    return {
        "po_total": po_total,
        "po_paid": po_paid,
        "outstanding": max(po_total - po_paid, ZERO),
    }


def revenue_summary():
    """Cash actually collected vs cash spent (rough P&L snapshot)."""
    # Collected = project advances + subsidy + extra project payments + AMC paid.
    project_collected = ZERO
    for p in Project.objects.all():
        project_collected += p.collected_amount
    amc_collected = _sum(AMCContract.objects.all(), "amount_paid")
    collected = project_collected + amc_collected

    # Spent = supplier payments (PO amount_paid) + general expenses.
    po_paid = _sum(PurchaseOrder.objects.all(), "amount_paid")
    expenses = _sum(Expense.objects.all(), "amount")
    spent = po_paid + expenses

    return {
        "collected": collected,
        "spent": spent,
        "net": collected - spent,
        "expenses": expenses,
        "po_paid": po_paid,
    }


def subsidy_summary():
    """Subsidy pipeline: claimed vs sanctioned vs disbursed."""
    qs = SubsidyClaim.objects.all()
    claimed = _sum(qs, "claimed_amount")
    sanctioned = _sum(qs, "sanctioned_amount")
    disbursed = _sum(qs, "disbursed_amount")
    return {
        "claimed": claimed,
        "sanctioned": sanctioned,
        "disbursed": disbursed,
        "pending_disbursement": max(sanctioned - disbursed, ZERO),
        "count": qs.count(),
        "disbursed_count": qs.filter(status=SubsidyStatus.DISBURSED).count(),
    }


def dashboard_context():
    """Everything the finance dashboard needs, in one call."""
    receivables = receivables_summary()
    payables = payables_summary()
    revenue = revenue_summary()
    subsidy = subsidy_summary()

    # Net-metering pipeline counts by status (for a quick progress view).
    nm_counts = {}
    for nm in NetMetering.objects.all():
        nm_counts[nm.status] = nm_counts.get(nm.status, 0) + 1

    return {
        "receivables": receivables,
        "payables": payables,
        "revenue": revenue,
        "subsidy": subsidy,
        "nm_counts": nm_counts,
        # A single headline "position": what we're owed minus what we owe.
        "net_position": receivables["total"] - payables["outstanding"],
    }
