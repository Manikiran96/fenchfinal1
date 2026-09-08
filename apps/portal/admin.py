from django.contrib import admin
from .models import StageUpdate, StagePhoto


class StagePhotoInline(admin.TabularInline):
    model = StagePhoto
    extra = 0


@admin.register(StageUpdate)
class StageUpdateAdmin(admin.ModelAdmin):
    list_display = ("project", "stage", "technician", "is_done", "created_at")
    list_filter = ("stage", "is_done")
    search_fields = ("project__project_number",)
    inlines = [StagePhotoInline]


admin.site.register(StagePhoto)
