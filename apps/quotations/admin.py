from django.contrib import admin
from .models import Quotation, QuotationItem


class QuotationItemInline(admin.TabularInline):
    model = QuotationItem
    extra = 0
    readonly_fields = ("amount",)


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ("quotation_number", "revision", "lead", "capacity_kw", "final_price", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("quotation_number", "lead__customer_name", "lead__lead_number")
    inlines = [QuotationItemInline]


admin.site.register(QuotationItem)
