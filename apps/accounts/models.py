from django.contrib.auth.models import AbstractUser
from django.db import models


class Branch(models.Model):
    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=20, unique=True)
    city = models.CharField(max_length=80, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Branches"

    def __str__(self):
        return f"{self.name} ({self.code})"


class Role(models.TextChoices):
    SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
    ADMIN = "ADMIN", "Admin"
    BRANCH_MANAGER = "BRANCH_MANAGER", "Branch Manager"
    SALES_MANAGER = "SALES_MANAGER", "Sales Manager"
    SALES_EXECUTIVE = "SALES_EXECUTIVE", "Sales Executive"
    PROJECT_MANAGER = "PROJECT_MANAGER", "Project Manager"
    ACCOUNTS = "ACCOUNTS", "Accounts Team"
    INVENTORY_MANAGER = "INVENTORY_MANAGER", "Inventory Manager"
    STORE_KEEPER = "STORE_KEEPER", "Store Keeper"
    PROCUREMENT = "PROCUREMENT", "Procurement Officer"
    TECHNICIAN = "TECHNICIAN", "Technician"
    SERVICE_ENGINEER = "SERVICE_ENGINEER", "Service Engineer"
    SUBSIDY_COORDINATOR = "SUBSIDY_COORDINATOR", "Subsidy Coordinator"
    CUSTOMER = "CUSTOMER", "Customer"


class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True)
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.SALES_EXECUTIVE)
    branch = models.ForeignKey(Branch, null=True, blank=True, on_delete=models.SET_NULL, related_name="users")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return f"{self.get_full_name() or self.username} [{self.get_role_display()}]"

    @property
    def is_sales(self):
        return self.role in {Role.SALES_MANAGER, Role.SALES_EXECUTIVE}

    @property
    def is_admin_level(self):
        return self.role in {Role.SUPER_ADMIN, Role.ADMIN, Role.BRANCH_MANAGER}

    @property
    def can_approve_quotation(self):
        return self.role in {Role.SUPER_ADMIN, Role.ADMIN, Role.BRANCH_MANAGER, Role.SALES_MANAGER}

    @property
    def can_manage_projects(self):
        return self.role in {Role.SUPER_ADMIN, Role.ADMIN, Role.BRANCH_MANAGER, Role.PROJECT_MANAGER}

    @property
    def can_manage_inventory(self):
        return self.role in {Role.SUPER_ADMIN, Role.ADMIN, Role.BRANCH_MANAGER, Role.INVENTORY_MANAGER, Role.STORE_KEEPER}

    @property
    def can_procure(self):
        return self.role in {Role.SUPER_ADMIN, Role.ADMIN, Role.BRANCH_MANAGER, Role.INVENTORY_MANAGER, Role.PROCUREMENT}

    @property
    def is_field_staff(self):
        return self.role in {Role.TECHNICIAN, Role.SERVICE_ENGINEER}

    @property
    def can_manage_service(self):
        return self.role in {Role.SUPER_ADMIN, Role.ADMIN, Role.BRANCH_MANAGER, Role.SERVICE_ENGINEER, Role.PROJECT_MANAGER}

    @property
    def can_manage_finance(self):
        """Can record payments/expenses and manage subsidy & net-metering."""
        return self.role in {Role.SUPER_ADMIN, Role.ADMIN, Role.BRANCH_MANAGER,
                             Role.ACCOUNTS, Role.SUBSIDY_COORDINATOR}


class LoginAudit(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="login_audits")
    email_attempted = models.EmailField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    success = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activities")
    action = models.CharField(max_length=120)
    detail = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
