from django.urls import path
from . import views

app_name = "customers"
urlpatterns = [
    path("", views.customer_list, name="customer_list"),
    path("rows/", views.customer_rows, name="customer_rows"),
    path("create/", views.customer_create, name="customer_create"),
    path("<int:pk>/", views.customer_detail, name="customer_detail"),
    path("<int:pk>/edit/", views.customer_edit, name="customer_edit"),
    path("<int:pk>/document/", views.upload_document, name="upload_document"),
    path("<int:pk>/note/", views.add_note, name="add_note"),
    path("document/<int:doc_id>/delete/", views.delete_document, name="delete_document"),
]
