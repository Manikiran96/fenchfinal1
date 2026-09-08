from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel


PAYMENT_MODES = [
    ("CASH", "Cash"), ("UPI", "UPI"), ("BANK", "Bank Transfer"),
    ("CHEQUE", "Cheque"), ("CARD", "Card"), ("NEFT", "NEFT/RTGS"),
]


# ---------------------------------------------------------------------------
# Payables — money we owe suppliers (settled against Purchase Orders)
# ---------------------------------------------------------------------------
class SupplierPayment(TimeStampedModel):
    """A payment made to a supplier against a Purchase Order.

    Recording one rolls up into the PO's `amount_paid`, which drives the
    payables dashboard (outstanding = PO total - amount_paid).
    """
    purchase_order = models.ForeignKey(
        "inventory.PurchaseOrder", on_delete=models.CASCADE, related_name="payments"
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    mode = models.CharField(max_length=10, choices=PAYMENT_MODES, default="BANK")
    reference = models.CharField(max_length=140, blank=True)
    paid_on = models.DateField(default=timezone.now)

    class Meta:
        ordering = ["-paid_on", "-created_at"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Keep the PO's amount_paid in sync with the sum of its payments.
        po = self.purchase_order
        total = sum((p.amount for p in po.payments.all()), Decimal("0"))
        po.amount_paid = total
        po.save(update_fields=["amount_paid"])

    def __str__(self):
        return f"{self.amount} to {self.purchase_order.supplier.name}"


# ---------------------------------------------------------------------------
# Receivables — money customers owe us on AMC contracts
# (project receivables already live on Project.pending_amount)
# ---------------------------------------------------------------------------
class AMCPayment(TimeStampedModel):
    """A payment received from a customer against an AMC contract."""
    amc = models.ForeignKey(
        "service.AMCContract", on_delete=models.CASCADE, related_name="payments"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    mode = models.CharField(max_length=10, choices=PAYMENT_MODES, default="BANK")
    reference = models.CharField(max_length=140, blank=True)
    paid_on = models.DateField(default=timezone.now)

    class Meta:
        ordering = ["-paid_on", "-created_at"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        amc = self.amc
        total = sum((p.amount for p in amc.payments.all()), Decimal("0"))
        amc.amount_paid = total
        amc.save(update_fields=["amount_paid"])

    def __str__(self):
        return f"{self.amount} for {self.amc.contract_number}"


# ---------------------------------------------------------------------------
# General expenses (overheads not tied to a PO)
# ---------------------------------------------------------------------------
class ExpenseCategory(models.TextChoices):
    SALARY = "SALARY", "Salaries"
    RENT = "RENT", "Rent"
    UTILITIES = "UTILITIES", "Utilities"
    TRANSPORT = "TRANSPORT", "Transport / Logistics"
    MARKETING = "MARKETING", "Marketing"
    TOOLS = "TOOLS", "Tools & Equipment"
    MISC = "MISC", "Miscellaneous"


class Expense(TimeStampedModel):
    expense_number = models.CharField(max_length=25, unique=True, editable=False)
    category = models.CharField(max_length=20, choices=ExpenseCategory.choices, default=ExpenseCategory.MISC)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    mode = models.CharField(max_length=10, choices=PAYMENT_MODES, default="BANK")
    project = models.ForeignKey("projects.Project", null=True, blank=True,
                                on_delete=models.SET_NULL, related_name="expenses")
    spent_on = models.DateField(default=timezone.now)

    class Meta:
        ordering = ["-spent_on", "-created_at"]

    def save(self, *args, **kwargs):
        if not self.expense_number:
            self.expense_number = self._generate_number()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_number():
        year = timezone.now().year
        last = Expense.objects.filter(expense_number__startswith=f"EXP{year}").order_by("-id").first()
        seq = int(last.expense_number[7:11]) + 1 if last else 1
        return f"EXP{year}{seq:04d}"

    def __str__(self):
        return f"{self.expense_number} - {self.description}"


# ---------------------------------------------------------------------------
# Subsidy tracking (claim -> sanction -> disbursement)
# ---------------------------------------------------------------------------
class SubsidyStatus(models.TextChoices):
    PENDING = "PENDING", "Application Pending"
    APPLIED = "APPLIED", "Applied"
    SANCTIONED = "SANCTIONED", "Sanctioned"
    DISBURSED = "DISBURSED", "Disbursed"
    REJECTED = "REJECTED", "Rejected"


class SubsidyClaim(TimeStampedModel):
    """Government subsidy claim tracked per project."""
    claim_number = models.CharField(max_length=25, unique=True, editable=False)
    project = models.OneToOneField("projects.Project", on_delete=models.CASCADE, related_name="subsidy_claim")

    claimed_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sanctioned_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    disbursed_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    status = models.CharField(max_length=12, choices=SubsidyStatus.choices, default=SubsidyStatus.PENDING)
    application_no = models.CharField(max_length=60, blank=True)
    applied_on = models.DateField(null=True, blank=True)
    sanctioned_on = models.DateField(null=True, blank=True)
    disbursed_on = models.DateField(null=True, blank=True)
    coordinator = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name="subsidy_claims")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.claim_number:
            self.claim_number = self._generate_number()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_number():
        year = timezone.now().year
        last = SubsidyClaim.objects.filter(claim_number__startswith=f"SUB{year}").order_by("-id").first()
        seq = int(last.claim_number[7:11]) + 1 if last else 1
        return f"SUB{year}{seq:04d}"

    @property
    def pending_disbursement(self):
        return (self.sanctioned_amount or Decimal("0")) - (self.disbursed_amount or Decimal("0"))

    def __str__(self):
        return f"{self.claim_number} - {self.project.project_number}"


# ---------------------------------------------------------------------------
# Net metering application tracking
# ---------------------------------------------------------------------------
class NetMeteringStatus(models.TextChoices):
    NOT_STARTED = "NOT_STARTED", "Not Started"
    APPLIED = "APPLIED", "Applied"
    INSPECTION = "INSPECTION", "Inspection Scheduled"
    APPROVED = "APPROVED", "Approved"
    METER_INSTALLED = "METER_INSTALLED", "Meter Installed"
    COMMISSIONED = "COMMISSIONED", "Commissioned"
    REJECTED = "REJECTED", "Rejected"


class NetMetering(TimeStampedModel):
    """Net-metering / DISCOM connection tracking per project."""
    project = models.OneToOneField("projects.Project", on_delete=models.CASCADE, related_name="net_metering")
    discom = models.CharField("DISCOM", max_length=120, blank=True)
    application_no = models.CharField(max_length=60, blank=True)
    consumer_no = models.CharField(max_length=60, blank=True)
    sanctioned_load_kw = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=16, choices=NetMeteringStatus.choices, default=NetMeteringStatus.NOT_STARTED)
    applied_on = models.DateField(null=True, blank=True)
    approved_on = models.DateField(null=True, blank=True)
    meter_installed_on = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Net Metering - {self.project.project_number}"
