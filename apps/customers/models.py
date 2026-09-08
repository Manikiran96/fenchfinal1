from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel


class Customer(TimeStampedModel):
    customer_code = models.CharField(max_length=20, unique=True, editable=False)
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    state = models.CharField(max_length=80, blank=True)
    district = models.CharField(max_length=80, blank=True)
    city = models.CharField(max_length=80, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    gst = models.CharField("GST", max_length=15, blank=True)
    pan = models.CharField("PAN", max_length=10, blank=True)
    aadhaar = models.CharField("Aadhaar", max_length=12, blank=True)
    source_lead = models.OneToOneField("crm.Lead", null=True, blank=True, on_delete=models.SET_NULL, related_name="customer")
    account_manager = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="managed_customers")
    portal_user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="customer_profile")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.customer_code:
            self.customer_code = self._generate_code()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_code():
        year = timezone.now().year
        last = Customer.objects.filter(customer_code__startswith=f"CUST{year}").order_by("-id").first()
        seq = int(last.customer_code[-4:]) + 1 if last else 1
        return f"CUST{year}{seq:04d}"

    def __str__(self):
        return f"{self.customer_code} - {self.name}"

    @property
    def has_portal_access(self):
        return self.portal_user_id is not None


class DocumentType(models.TextChoices):
    AADHAAR = "AADHAAR", "Aadhaar Card"
    PAN = "PAN", "PAN Card"
    GST = "GST", "GST Certificate"
    ELECTRICITY_BILL = "ELECTRICITY_BILL", "Electricity Bill"
    AGREEMENT = "AGREEMENT", "Signed Agreement"
    SITE_PHOTO = "SITE_PHOTO", "Site Photo"
    OTHER = "OTHER", "Other"


class CustomerDocument(TimeStampedModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="documents")
    doc_type = models.CharField(max_length=20, choices=DocumentType.choices, default=DocumentType.OTHER)
    file = models.FileField(upload_to="customers/documents/")
    label = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["-created_at"]


class CustomerNote(TimeStampedModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="notes")
    note = models.TextField()

    class Meta:
        ordering = ["-created_at"]
