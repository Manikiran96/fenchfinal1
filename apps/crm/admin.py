from django.contrib import admin
from .models import Lead, LeadActivity, LeadAttachment


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("lead_number", "customer_name", "mobile", "status", "assigned_to", "is_converted", "created_at")
    list_filter = ("status", "source", "is_converted")
    search_fields = ("lead_number", "customer_name", "mobile", "email")


admin.site.register(LeadActivity)
admin.site.register(LeadAttachment)
