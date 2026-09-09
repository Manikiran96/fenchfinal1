from django.urls import path
from . import views

app_name = "portal"

urlpatterns = [
    # entry point — routes to the right portal by role
    path("", views.portal_home, name="home"),

    # ---------- Sales portal ----------
    path("sales/", views.sales_dashboard, name="sales_dashboard"),
    path("sales/leads/", views.sales_lead_list, name="sales_lead_list"),
    path("sales/leads/new/", views.sales_lead_create, name="sales_lead_create"),
    path("sales/leads/<int:pk>/", views.sales_lead_detail, name="sales_lead_detail"),
    path("sales/leads/<int:pk>/followup/", views.sales_add_followup, name="sales_add_followup"),
    # admin monitoring
    path("sales/today/", views.sales_today_admin, name="sales_today_admin"),

    # ---------- Technician portal ----------
    path("tech/", views.tech_dashboard, name="tech_dashboard"),
    path("tech/projects/", views.tech_project_list, name="tech_project_list"),
    path("tech/projects/<int:pk>/", views.tech_project_detail, name="tech_project_detail"),
    path("tech/projects/<int:pk>/update/", views.tech_stage_update, name="tech_stage_update"),
]
