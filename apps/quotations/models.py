from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel


class QuotationStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    PENDING_APPROVAL = "PENDING_APPROVAL", "Pending Approval"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    SENT = "SENT", "Sent to Customer"


class Quotation(TimeStampedModel):
    quotation_number = models.CharField(max_length=25, unique=True, editable=False)
    lead = models.ForeignKey("crm.Lead", on_delete=models.CASCADE, related_name="quotations")
    revision = models.PositiveIntegerField(default=1)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="revisions")
    capacity_kw = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    panel_brand = models.CharField(max_length=120, blank=True)
    inverter_brand = models.CharField(max_length=120, blank=True)
    material_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("18.00"))
    subsidy_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    base_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quotation_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    final_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=QuotationStatus.choices, default=QuotationStatus.DRAFT)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="approved_quotations")
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.CharField(max_length=255, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.quotation_number:
            self.quotation_number = self._generate_number()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_number():
        year = timezone.now().year
        last = Quotation.objects.filter(quotation_number__startswith=f"QT{year}").order_by("-id").first()
        seq = int(last.quotation_number[6:10]) + 1 if last else 1
        return f"QT{year}{seq:04d}"

    def recalculate(self, commit=True):
        items_total = sum((i.amount for i in self.items.all()), Decimal("0"))
        self.base_amount = (self.material_cost or Decimal("0")) + items_total
        self.tax_amount = (self.base_amount * (self.tax_percent or Decimal("0")) / Decimal("100")).quantize(Decimal("0.01"))
        self.quotation_value = self.base_amount + self.tax_amount
        self.final_price = self.quotation_value - (self.subsidy_amount or Decimal("0"))
        if commit:
            super().save(update_fields=["base_amount", "tax_amount", "quotation_value", "final_price"])

    @property
    def is_editable(self):
        return self.status in {QuotationStatus.DRAFT, QuotationStatus.REJECTED}

    @property
    def can_send(self):
        return self.status == QuotationStatus.APPROVED

    def submit_for_approval(self):
        self.status = QuotationStatus.PENDING_APPROVAL
        self.save(update_fields=["status"])

    def approve(self, user):
        self.status = QuotationStatus.APPROVED
        self.approved_by = user
        self.approved_at = timezone.now()
        self.rejection_reason = ""
        self.save(update_fields=["status", "approved_by", "approved_at", "rejection_reason"])

    def reject(self, user, reason=""):
        self.status = QuotationStatus.REJECTED
        self.approved_by = user
        self.rejection_reason = reason[:255]
        self.save(update_fields=["status", "approved_by", "rejection_reason"])

    def mark_sent(self):
        self.status = QuotationStatus.SENT
        self.sent_at = timezone.now()
        self.save(update_fields=["status", "sent_at"])

    def __str__(self):
        return f"{self.quotation_number} (rev {self.revision})"


class QuotationItem(TimeStampedModel):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name="items")
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)

    class Meta:
        ordering = ["id"]

    def save(self, *args, **kwargs):
        self.amount = (self.quantity or 0) * (self.unit_price or 0)
        super().save(*args, **kwargs)
