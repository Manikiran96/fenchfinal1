from django.urls import path

from . import views

app_name = "projects"
urlpatterns = [
    path("", views.project_list, name="project_list"),
    path("rows/", views.project_rows, name="project_rows"),
    path("create/", views.project_create, name="project_create"),
    path("<int:pk>/", views.project_detail, name="project_detail"),
    path("<int:pk>/edit/", views.project_edit, name="project_edit"),
    path("<int:pk>/milestone/", views.add_milestone, name="add_milestone"),
    path("<int:pk>/payment/", views.add_payment, name="add_payment"),
    path("<int:pk>/documents/upload/", views.document_upload, name="document_upload"),
    path("documents/<int:doc_id>/download/", views.document_download, name="document_download"),
    path("documents/<int:doc_id>/delete/", views.document_delete, name="document_delete"),
]
