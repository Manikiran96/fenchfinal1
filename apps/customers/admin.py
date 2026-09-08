from django.contrib import admin
from .models import Customer, CustomerDocument, CustomerNote


class CustomerDocumentInline(admin.TabularInline):
    model = CustomerDocument
    extra = 0


class CustomerNoteInline(admin.TabularInline):
    model = CustomerNote
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("customer_code", "name", "phone", "city", "account_manager", "has_portal_access", "is_active", "created_at")
    list_filter = ("is_active", "state", "city")
    search_fields = ("customer_code", "name", "phone", "email", "gst", "pan")
    inlines = [CustomerDocumentInline, CustomerNoteInline]


admin.site.register(CustomerDocument)
admin.site.register(CustomerNote)
