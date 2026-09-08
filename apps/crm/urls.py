from django.urls import path
from . import views

app_name = "crm"
urlpatterns = [
    path("leads/", views.lead_list, name="lead_list"),
    path("leads/rows/", views.lead_rows, name="lead_rows"),
    path("leads/create/", views.lead_create, name="lead_create"),
    path("leads/<int:pk>/", views.lead_detail, name="lead_detail"),
    path("leads/<int:pk>/edit/", views.lead_edit, name="lead_edit"),
    path("leads/<int:pk>/activity/", views.add_activity, name="add_activity"),
]
