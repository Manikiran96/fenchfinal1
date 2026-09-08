from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Branch, LoginAudit, ActivityLog


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("email", "username", "role", "branch", "is_active")
    list_filter = ("role", "branch", "is_active")
    fieldsets = UserAdmin.fieldsets + (("ERP profile", {"fields": ("phone", "role", "branch")}),)


admin.site.register(Branch)
admin.site.register(LoginAudit)
admin.site.register(ActivityLog)
