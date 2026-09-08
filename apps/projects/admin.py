from django.contrib import admin
from .models import Project, ProjectMilestone, ProjectPayment


class MilestoneInline(admin.TabularInline):
    model = ProjectMilestone
    extra = 0


class PaymentInline(admin.TabularInline):
    model = ProjectPayment
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("project_number", "customer", "capacity_kw", "project_value", "advance_amount", "pending_amount", "stage", "created_at")
    list_filter = ("stage", "project_type", "category")
    search_fields = ("project_number", "customer__name", "customer__customer_code")
    inlines = [MilestoneInline, PaymentInline]


admin.site.register(ProjectMilestone)
admin.site.register(ProjectPayment)
