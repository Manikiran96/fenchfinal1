from django.urls import path
from . import views

app_name = "inventory"
urlpatterns = [
    path("", views.item_list, name="item_list"),
    path("items/rows/", views.item_rows, name="item_rows"),
    path("items/create/", views.item_create, name="item_create"),
    path("items/<int:pk>/", views.item_detail, name="item_detail"),
    path("items/<int:pk>/edit/", views.item_edit, name="item_edit"),
    path("items/<int:pk>/adjust/", views.adjust_stock, name="adjust_stock"),
    path("items/<int:pk>/issue/", views.issue_stock, name="issue_stock"),
    path("warehouses/", views.warehouse_list, name="warehouse_list"),
    path("warehouses/create/", views.warehouse_create, name="warehouse_create"),
    path("suppliers/", views.supplier_list, name="supplier_list"),
    path("suppliers/create/", views.supplier_create, name="supplier_create"),
    path("po/", views.po_list, name="po_list"),
    path("po/create/", views.po_create, name="po_create"),
    path("po/<int:pk>/", views.po_detail, name="po_detail"),
    path("po/<int:pk>/place/", views.po_place, name="po_place"),
    path("po/<int:pk>/receive/", views.po_receive, name="po_receive"),
]
