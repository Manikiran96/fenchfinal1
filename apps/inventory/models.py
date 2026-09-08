from decimal import Decimal
from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel


class Warehouse(TimeStampedModel):
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=20, unique=True)
    address = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Supplier(TimeStampedModel):
    name = models.CharField(max_length=150)
    contact_person = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    gst = models.CharField("GST", max_length=15, blank=True)
    address = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ItemCategory(models.TextChoices):
    PANEL = "PANEL", "Solar Panel"
    INVERTER = "INVERTER", "Inverter"
    BATTERY = "BATTERY", "Battery"
    STRUCTURE = "STRUCTURE", "Mounting Structure"
    CABLE = "CABLE", "Cable & Wiring"
    BOS = "BOS", "Balance of System"
    METER = "METER", "Meter"
    OTHER = "OTHER", "Other"


class Item(TimeStampedModel):
    sku = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=180)
    category = models.CharField(max_length=20, choices=ItemCategory.choices, default=ItemCategory.OTHER)
    unit = models.CharField(max_length=20, default="pcs")
    brand = models.CharField(max_length=120, blank=True)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.sku} - {self.name}"

    @property
    def total_stock(self):
        agg = self.stocks.aggregate(t=models.Sum("quantity"))
        return agg["t"] or Decimal("0")

    @property
    def is_low_stock(self):
        return self.total_stock <= (self.reorder_level or Decimal("0"))


class Stock(TimeStampedModel):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="stocks")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="stocks")
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        unique_together = ("item", "warehouse")
        ordering = ["item__name"]


class MovementType(models.TextChoices):
    IN = "IN", "Stock In"
    OUT = "OUT", "Stock Out"
    ADJUST = "ADJUST", "Adjustment"
    TRANSFER = "TRANSFER", "Transfer"


class StockMovement(TimeStampedModel):
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name="movements")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="movements")
    movement_type = models.CharField(max_length=10, choices=MovementType.choices)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reference = models.CharField(max_length=140, blank=True)
    project = models.ForeignKey("projects.Project", null=True, blank=True, on_delete=models.SET_NULL, related_name="stock_movements")

    class Meta:
        ordering = ["-created_at"]


class POStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    ORDERED = "ORDERED", "Ordered"
    PARTIAL = "PARTIAL", "Partially Received"
    RECEIVED = "RECEIVED", "Received"
    CANCELLED = "CANCELLED", "Cancelled"


class PurchaseOrder(TimeStampedModel):
    po_number = models.CharField(max_length=25, unique=True, editable=False)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="purchase_orders")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="purchase_orders")
    status = models.CharField(max_length=10, choices=POStatus.choices, default=POStatus.DRAFT)
    expected_date = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.po_number:
            self.po_number = self._generate_number()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_number():
        year = timezone.now().year
        last = PurchaseOrder.objects.filter(po_number__startswith=f"PO{year}").order_by("-id").first()
        seq = int(last.po_number[6:10]) + 1 if last else 1
        return f"PO{year}{seq:04d}"

    def recalculate_total(self, commit=True):
        total = sum((li.amount for li in self.lines.all()), Decimal("0"))
        self.total_amount = total
        if commit:
            super().save(update_fields=["total_amount"])

    @property
    def payable_balance(self):
        return (self.total_amount or Decimal("0")) - (self.amount_paid or Decimal("0"))

    @property
    def is_editable(self):
        return self.status == POStatus.DRAFT

    def __str__(self):
        return f"{self.po_number} - {self.supplier.name}"


class PurchaseOrderLine(TimeStampedModel):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="lines")
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name="po_lines")
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=0, editable=False)
    received_qty = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ["id"]

    def save(self, *args, **kwargs):
        self.amount = (self.quantity or 0) * (self.unit_price or 0)
        super().save(*args, **kwargs)

    @property
    def pending_qty(self):
        return (self.quantity or Decimal("0")) - (self.received_qty or Decimal("0"))
