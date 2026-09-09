from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect


@login_required
def dashboard(request):
    u = request.user
    if u.is_sales:
        return redirect("portal:sales_dashboard")
    if u.is_field_staff:
        return redirect("portal:tech_dashboard")
    return render(request, "core/dashboard.html")   # admins/others → desktop ERP