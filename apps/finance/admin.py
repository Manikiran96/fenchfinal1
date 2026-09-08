from django.contrib import admin
from .models import SupplierPayment, AMCPayment, Expense, SubsidyClaim, NetMetering


@admin.register(SupplierPayment)
class SupplierPaymentAdmin(admin.ModelAdmin):
    list_display = ("purchase_order", "amount", "mode", "paid_on")
    search_fields = ("purchase_order__po_number", "reference")


@admin.register(AMCPayment)
class AMCPaymentAdmin(admin.ModelAdmin):
    list_display = ("amc", "amount", "mode", "paid_on")
    search_fields = ("amc__contract_number", "reference")


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("expense_number", "category", "description", "amount", "project", "spent_on")
    list_filter = ("category",)
    search_fields = ("expense_number", "description")


@admin.register(SubsidyClaim)
class SubsidyClaimAdmin(admin.ModelAdmin):
    list_display = ("claim_number", "project", "claimed_amount", "sanctioned_amount", "disbursed_amount", "status")
    list_filter = ("status",)
    search_fields = ("claim_number", "project__project_number", "application_no")


@admin.register(NetMetering)
class NetMeteringAdmin(admin.ModelAdmin):
    list_display = ("project", "discom", "application_no", "status", "applied_on", "approved_on")
    list_filter = ("status",)
    search_fields = ("project__project_number", "application_no", "consumer_no")
