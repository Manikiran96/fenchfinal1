from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel


class LeadStatus(models.TextChoices):
    NEW = "NEW", "New"
    CONTACTED = "CONTACTED", "Contacted"
    QUALIFIED = "QUALIFIED", "Qualified"
    SITE_VISIT = "SITE_VISIT", "Site Visit"
    QUOTATION_SENT = "QUOTATION_SENT", "Quotation Sent"
    NEGOTIATION = "NEGOTIATION", "Negotiation"
    WON = "WON", "Won"
    LOST = "LOST", "Lost"


class LeadSource(models.TextChoices):
    WEBSITE = "WEBSITE", "Website"
    REFERRAL = "REFERRAL", "Referral"
    WALK_IN = "WALK_IN", "Walk-in"
    CALL = "CALL", "Phone Call"
    SOCIAL = "SOCIAL", "Social Media"
    EXHIBITION = "EXHIBITION", "Exhibition"
    OTHER = "OTHER", "Other"


class Lead(TimeStampedModel):
    lead_number = models.CharField(max_length=20, unique=True, editable=False)
    customer_name = models.CharField(max_length=150)
    mobile = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    state = models.CharField(max_length=80, blank=True)
    district = models.CharField(max_length=80, blank=True)
    city = models.CharField(max_length=80, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    source = models.CharField(max_length=20, choices=LeadSource.choices, default=LeadSource.OTHER)
    expected_capacity_kw = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    expected_budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    remarks = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=LeadStatus.choices, default=LeadStatus.NEW)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name="assigned_leads")
    is_converted = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.lead_number:
            self.lead_number = self._generate_lead_number()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_lead_number():
        year = timezone.now().year
        last = Lead.objects.filter(lead_number__startswith=f"LD{year}").order_by("-id").first()
        seq = int(last.lead_number[-4:]) + 1 if last else 1
        return f"LD{year}{seq:04d}"

    @property
    def latest_quotation(self):
        return self.quotations.order_by("-created_at").first()

    def __str__(self):
        return f"{self.lead_number} - {self.customer_name}"


class LeadActivity(TimeStampedModel):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="activities")
    note = models.TextField()
    next_follow_up = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


class LeadAttachment(TimeStampedModel):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="leads/attachments/")
    label = models.CharField(max_length=120, blank=True)
