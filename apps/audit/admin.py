from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "module", "action", "model_name", "object_repr", "user_label")
    list_filter = ("module", "action", "model_name")
    search_fields = ("object_repr", "user_label", "model_name")
    readonly_fields = ("module", "object_repr", "model_name", "object_id",
                       "action", "changes", "user", "user_label", "created_at")

    def has_add_permission(self, request):
        return False  # audit rows are system-generated only
