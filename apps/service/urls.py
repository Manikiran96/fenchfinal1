from django.urls import path
from . import views

app_name = "service"
urlpatterns = [
    path("", views.ticket_list, name="ticket_list"),
    path("tickets/rows/", views.ticket_rows, name="ticket_rows"),
    path("tickets/create/", views.ticket_create, name="ticket_create"),
    path("tickets/<int:pk>/", views.ticket_detail, name="ticket_detail"),
    path("tickets/<int:pk>/assign/", views.ticket_assign, name="ticket_assign"),
    path("tickets/<int:pk>/status/", views.ticket_status, name="ticket_status"),
    path("tickets/<int:pk>/update/", views.ticket_update, name="ticket_update"),
    path("technicians/", views.technician_list, name="technician_list"),
    path("technicians/create/", views.technician_create, name="technician_create"),
    path("amc/", views.amc_list, name="amc_list"),
    path("amc/create/", views.amc_create, name="amc_create"),
    path("amc/<int:pk>/", views.amc_detail, name="amc_detail"),
    path("amc/<int:pk>/generate-visits/", views.amc_generate_visits, name="amc_generate_visits"),
    path("amc/visit/<int:visit_id>/complete/", views.amc_complete_visit, name="amc_complete_visit"),
]
