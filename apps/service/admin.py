from django.contrib import admin
from .models import Technician, ServiceTicket, TicketUpdate, AMCContract, AMCVisit


@admin.register(Technician)
class TechnicianAdmin(admin.ModelAdmin):
    list_display = ("employee_code", "display_name", "phone", "is_available", "open_ticket_count")
    search_fields = ("employee_code", "user__username", "user__email")


class TicketUpdateInline(admin.TabularInline):
    model = TicketUpdate
    extra = 0


@admin.register(ServiceTicket)
class ServiceTicketAdmin(admin.ModelAdmin):
    list_display = ("ticket_number", "title", "customer", "priority", "status", "assigned_to", "due_at", "is_overdue", "created_at")
    list_filter = ("status", "priority", "category")
    search_fields = ("ticket_number", "title", "customer__name")
    inlines = [TicketUpdateInline]


class AMCVisitInline(admin.TabularInline):
    model = AMCVisit
    extra = 0


@admin.register(AMCContract)
class AMCContractAdmin(admin.ModelAdmin):
    list_display = ("contract_number", "customer", "start_date", "end_date", "amount", "amount_paid", "status", "visits_done", "is_active")
    list_filter = ("status",)
    search_fields = ("contract_number", "customer__name")
    inlines = [AMCVisitInline]


admin.site.register(TicketUpdate)
admin.site.register(AMCVisit)
