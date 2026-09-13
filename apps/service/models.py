from datetime import timedelta
from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel
from apps.projects.storage_paths import ticket_photo_path   # noqa


class Technician(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="technician_profile")
    employee_code = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=15, blank=True)
    skills = models.CharField(max_length=255, blank=True)
    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ["employee_code"]

    def __str__(self):
        return f"{self.employee_code} - {self.display_name}"

    @property
    def display_name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def open_ticket_count(self):
        return self.tickets.exclude(status__in=[TicketStatus.RESOLVED, TicketStatus.CLOSED, TicketStatus.CANCELLED]).count()


class TicketPriority(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"
    CRITICAL = "CRITICAL", "Critical"


class TicketCategory(models.TextChoices):
    NEWPROJECT = "NEWPROJECT","New Project"
    INVERTER = "INVERTER", "Inverter Fault"
    PANEL = "PANEL", "Panel Issue"
    WIRING = "WIRING", "Wiring / Electrical"
    GENERATION = "GENERATION", "Low Generation"
    NET_METERING = "NET_METERING", "Net Metering"
    CLEANING = "CLEANING", "Cleaning / Maintenance"
    OTHER = "OTHER", "Other"


class TicketStatus(models.TextChoices):
    OPEN = "OPEN", "Open"
    ASSIGNED = "ASSIGNED", "Assigned"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    ON_HOLD = "ON_HOLD", "On Hold"
    RESOLVED = "RESOLVED", "Resolved"
    CLOSED = "CLOSED", "Closed"
    CANCELLED = "CANCELLED", "Cancelled"


SLA_HOURS = {TicketPriority.CRITICAL: 4, TicketPriority.HIGH: 24, TicketPriority.MEDIUM: 72, TicketPriority.LOW: 168}
OPEN_STATUSES = {TicketStatus.OPEN, TicketStatus.ASSIGNED, TicketStatus.IN_PROGRESS, TicketStatus.ON_HOLD}


class ServiceTicket(TimeStampedModel):
    ticket_number = models.CharField(max_length=25, unique=True, editable=False)
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="tickets")
    project = models.ForeignKey("projects.Project", null=True, blank=True, on_delete=models.SET_NULL, related_name="tickets")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=TicketCategory.choices, default=TicketCategory.OTHER)
    priority = models.CharField(max_length=10, choices=TicketPriority.choices, default=TicketPriority.MEDIUM)
    status = models.CharField(max_length=15, choices=TicketStatus.choices, default=TicketStatus.OPEN)
    assigned_to = models.ForeignKey(Technician, null=True, blank=True, on_delete=models.SET_NULL, related_name="tickets")
    due_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution = models.TextField(blank=True)
    amc = models.ForeignKey("service.AMCContract", null=True, blank=True, on_delete=models.SET_NULL, related_name="tickets")

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            self.ticket_number = self._generate_number()
        if not self.due_at:
            hours = SLA_HOURS.get(self.priority, 72)
            self.due_at = timezone.now() + timedelta(hours=hours)
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_number():
        year = timezone.now().year
        last = ServiceTicket.objects.filter(ticket_number__startswith=f"TKT{year}").order_by("-id").first()
        seq = int(last.ticket_number[7:11]) + 1 if last else 1
        return f"TKT{year}{seq:04d}"

    @property
    def is_open(self):
        return self.status in OPEN_STATUSES

    @property
    def is_overdue(self):
        if not self.due_at or not self.is_open:
            return False
        return timezone.now() > self.due_at

    def __str__(self):
        return f"{self.ticket_number} - {self.title}"


class TicketUpdate(TimeStampedModel):
    ticket = models.ForeignKey(ServiceTicket, on_delete=models.CASCADE, related_name="updates")
    note = models.TextField()
    old_status = models.CharField(max_length=15, blank=True)
    new_status = models.CharField(max_length=15, blank=True)

    class Meta:
        ordering = ["-created_at"]


class AMCStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    EXPIRED = "EXPIRED", "Expired"
    CANCELLED = "CANCELLED", "Cancelled"


class AMCContract(TimeStampedModel):
    contract_number = models.CharField(max_length=25, unique=True, editable=False)
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="amc_contracts")
    project = models.ForeignKey("projects.Project", null=True, blank=True, on_delete=models.SET_NULL, related_name="amc_contracts")
    start_date = models.DateField()
    end_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    visits_per_year = models.PositiveIntegerField(default=4)
    status = models.CharField(max_length=10, choices=AMCStatus.choices, default=AMCStatus.ACTIVE)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.contract_number:
            self.contract_number = self._generate_number()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_number():
        year = timezone.now().year
        last = AMCContract.objects.filter(contract_number__startswith=f"AMC{year}").order_by("-id").first()
        seq = int(last.contract_number[7:11]) + 1 if last else 1
        return f"AMC{year}{seq:04d}"

    @property
    def is_active(self):
        today = timezone.now().date()
        return self.status == AMCStatus.ACTIVE and self.start_date <= today <= self.end_date

    @property
    def is_expiring_soon(self):
        if self.status != AMCStatus.ACTIVE:
            return False
        today = timezone.now().date()
        return today <= self.end_date <= today + timedelta(days=30)

    @property
    def amc_balance(self):
        from decimal import Decimal
        return (self.amount or Decimal("0")) - (self.amount_paid or Decimal("0"))

    @property
    def visits_done(self):
        return self.visits.filter(is_done=True).count()

    def __str__(self):
        return f"{self.contract_number} - {self.customer.name}"


class AMCVisit(TimeStampedModel):
    amc = models.ForeignKey(AMCContract, on_delete=models.CASCADE, related_name="visits")
    scheduled_date = models.DateField()
    technician = models.ForeignKey(Technician, null=True, blank=True, on_delete=models.SET_NULL, related_name="amc_visits")
    is_done = models.BooleanField(default=False)
    done_on = models.DateField(null=True, blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ["scheduled_date"]

    @property
    def is_overdue(self):
        return (not self.is_done) and self.scheduled_date < timezone.now().date()
class TicketPhoto(TimeStampedModel):
    """A photo attached to a service-ticket update (before/after work)."""
    ticket_update = models.ForeignKey(
        "service.TicketUpdate", on_delete=models.CASCADE, related_name="photos"
    )
    image = models.ImageField(upload_to=ticket_photo_path)
    caption = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Photo for ticket update {self.ticket_update_id}"
