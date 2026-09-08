from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel
from apps.audit.mixins import AuditableModel


class ProjectType(models.TextChoices):
    ON_GRID = "ON_GRID", "On-Grid"
    OFF_GRID = "OFF_GRID", "Off-Grid"
    HYBRID = "HYBRID", "Hybrid"


class ProjectCategory(models.TextChoices):
    RESIDENTIAL = "RESIDENTIAL", "Residential"
    COMMERCIAL = "COMMERCIAL", "Commercial"
    INDUSTRIAL = "INDUSTRIAL", "Industrial"
    GOVERNMENT = "GOVERNMENT", "Government"


class ProjectStage(models.TextChoices):
    REGISTERED = "REGISTERED", "Registered"
    SURVEY = "SURVEY", "Site Survey"
    DESIGN = "DESIGN", "Design & Approval"
    MATERIAL_DISPATCH = "MATERIAL_DISPATCH", "Material Dispatch"
    INSTALLATION = "INSTALLATION", "Installation"
    NET_METERING = "NET_METERING", "Net Metering"
    COMMISSIONED = "COMMISSIONED", "Commissioned"
    CLOSED = "CLOSED", "Closed"


class Project(AuditableModel,TimeStampedModel):
    AUDIT_MODULE = "projects"
    project_number = models.CharField(max_length=25, unique=True, editable=False)
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="projects")
    quotation = models.ForeignKey("quotations.Quotation", null=True, blank=True, on_delete=models.SET_NULL, related_name="projects")
    project_type = models.CharField(max_length=20, choices=ProjectType.choices, default=ProjectType.ON_GRID)
    category = models.CharField(max_length=20, choices=ProjectCategory.choices, default=ProjectCategory.RESIDENTIAL)
    capacity_kw = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    project_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subsidy_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    advance_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pending_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    location = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    stage = models.CharField(max_length=20, choices=ProjectStage.choices, default=ProjectStage.REGISTERED)
    project_manager = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="managed_projects")
    technicians = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="field_projects",limit_choices_to={"role": "TECHNICIAN"},)
    expected_completion = models.DateField(null=True, blank=True)
    commissioned_on = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.project_number:
            self.project_number = self._generate_number()
        self.pending_amount = self._compute_pending()
        super().save(*args, **kwargs)

    def _compute_pending(self):
        extra = Decimal("0")
        if self.pk:
            extra = sum((p.amount for p in self.payments.all()), Decimal("0"))
        return ((self.project_value or Decimal("0")) - (self.subsidy_amount or Decimal("0")) - (self.advance_amount or Decimal("0")) - extra)

    @staticmethod
    def _generate_number():
        year = timezone.now().year
        last = Project.objects.filter(project_number__startswith=f"PRJ{year}").order_by("-id").first()
        seq = int(last.project_number[7:11]) + 1 if last else 1
        return f"PRJ{year}{seq:04d}"

    @property
    def collected_amount(self):
        extra = sum((p.amount for p in self.payments.all()), Decimal("0"))
        return (self.subsidy_amount or Decimal("0")) + (self.advance_amount or Decimal("0")) + extra

    @property
    def balance_due(self):
        return (self.project_value or Decimal("0")) - self.collected_amount

    @property
    def progress_percent(self):
        order = list(ProjectStage.values)
        try:
            idx = order.index(self.stage)
        except ValueError:
            idx = 0
        return int(round((idx / (len(order) - 1)) * 100))

    def __str__(self):
        return f"{self.project_number} - {self.customer.name}"


class ProjectMilestone(TimeStampedModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="milestones")
    stage = models.CharField(max_length=20, choices=ProjectStage.choices)
    title = models.CharField(max_length=150)
    note = models.TextField(blank=True)
    is_done = models.BooleanField(default=False)
    done_on = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


class ProjectPayment(TimeStampedModel):
    MODE_CHOICES = [("CASH", "Cash"), ("UPI", "UPI"), ("BANK", "Bank Transfer"), ("CHEQUE", "Cheque"), ("CARD", "Card")]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default="BANK")
    reference = models.CharField(max_length=120, blank=True)
    paid_on = models.DateField(default=timezone.now)

    class Meta:
        ordering = ["-paid_on", "-created_at"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.project.save(update_fields=["pending_amount"])
class ProjectDocumentCategory(models.TextChoices):
    AGREEMENT = "AGREEMENT", "Agreement / Contract"
    DESIGN = "DESIGN", "Design / Drawing"
    APPROVAL = "APPROVAL", "Govt Approval"
    SUBSIDY = "SUBSIDY", "Subsidy Papers"
    INVOICE = "INVOICE", "Invoice / Bill"
    SITE_PHOTO = "SITE_PHOTO", "Site Photo"
    HANDOVER = "HANDOVER", "Handover Document"
    OTHER = "OTHER", "Other"


class ProjectDocument(TimeStampedModel):
    """A file stored against a project. Supports view / download / delete."""
    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="documents"
    )
    category = models.CharField(
        max_length=20, choices=ProjectDocumentCategory.choices,
        default=ProjectDocumentCategory.OTHER,
    )
    title = models.CharField(max_length=160)
    file = models.FileField(upload_to="projects/documents/")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="uploaded_project_docs",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.project.project_number})"

    @property
    def filename(self):
        import os
        return os.path.basename(self.file.name)
