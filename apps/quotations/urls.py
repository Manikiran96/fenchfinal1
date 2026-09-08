from django.urls import path
from . import views

app_name = "quotations"
urlpatterns = [
    path("", views.quotation_list, name="quotation_list"),
    path("rows/", views.quotation_rows, name="quotation_rows"),
    path("lead/<int:lead_id>/create/", views.quotation_create, name="quotation_create"),
    path("<int:pk>/", views.quotation_detail, name="quotation_detail"),
    path("<int:pk>/edit/", views.quotation_edit, name="quotation_edit"),
    path("<int:pk>/submit/", views.quotation_submit, name="quotation_submit"),
    path("<int:pk>/approve/", views.quotation_approve, name="quotation_approve"),
    path("<int:pk>/reject/", views.quotation_reject, name="quotation_reject"),
    path("<int:pk>/revise/", views.quotation_revise, name="quotation_revise"),
    path("<int:pk>/pdf/", views.quotation_pdf, name="quotation_pdf"),
    path("<int:pk>/print/", views.quotation_print, name="quotation_print"),
    path("<int:pk>/send/", views.quotation_send, name="quotation_send"),
]
