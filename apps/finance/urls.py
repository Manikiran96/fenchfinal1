from django.urls import path
from . import views

app_name = "finance"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    # Receivables / Payables
    path("receivables/", views.receivables, name="receivables"),
    path("payables/", views.payables, name="payables"),
    path("payables/<int:po_id>/pay/", views.pay_supplier, name="pay_supplier"),
    path("amc/<int:amc_id>/pay/", views.pay_amc, name="pay_amc"),
    # Expenses
    path("expenses/", views.expense_list, name="expense_list"),
    path("expenses/create/", views.expense_create, name="expense_create"),
    # Subsidy
    path("subsidy/", views.subsidy_list, name="subsidy_list"),
    path("subsidy/create/", views.subsidy_create, name="subsidy_create"),
    path("subsidy/<int:pk>/edit/", views.subsidy_edit, name="subsidy_edit"),
    # Net metering
    path("net-metering/", views.netmetering_list, name="netmetering_list"),
    path("net-metering/create/", views.netmetering_create, name="netmetering_create"),
    path("net-metering/<int:pk>/edit/", views.netmetering_edit, name="netmetering_edit"),
]
