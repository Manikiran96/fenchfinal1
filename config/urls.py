from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("crm/", include("apps.crm.urls")),
    path("quotations/", include("apps.quotations.urls")),
    path("customers/", include("apps.customers.urls")),
    path("projects/", include("apps.projects.urls")),
    path("inventory/", include("apps.inventory.urls")),
    path("service/", include("apps.service.urls")),
    path("finance/", include("apps.finance.urls")),
    path("api/auth/", include("apps.accounts.api_urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
