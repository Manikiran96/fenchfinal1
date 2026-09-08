"""Inventory / Procurement / Warehouse views (Module 6)."""
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string

from apps.accounts.permissions import role_required
from apps.accounts.models import Role
from apps.projects.models import Project
from .models import Item, Warehouse, Supplier, Stock, ItemCategory, PurchaseOrder, POStatus
from .forms import (ItemForm, WarehouseForm, SupplierForm, AdjustStockForm, IssueToProjectForm, PurchaseOrderForm, POLineFormSet)
from . import services

VIEW_ROLES = (Role.SUPER_ADMIN, Role.ADMIN, Role.BRANCH_MANAGER, Role.INVENTORY_MANAGER, Role.STORE_KEEPER, Role.PROCUREMENT, Role.PROJECT_MANAGER)
STOCK_ROLES = (Role.SUPER_ADMIN, Role.ADMIN, Role.BRANCH_MANAGER, Role.INVENTORY_MANAGER, Role.STORE_KEEPER)
PROCURE_ROLES = (Role.SUPER_ADMIN, Role.ADMIN, Role.BRANCH_MANAGER, Role.INVENTORY_MANAGER, Role.PROCUREMENT)


@role_required(*VIEW_ROLES)
def item_list(request):
    return render(request, "inventory/item_list.html", {"items": Item.objects.all(), "categories": ItemCategory.choices})


@role_required(*VIEW_ROLES)
def item_rows(request):
    items = Item.objects.all()
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    low = request.GET.get("low", "").strip()
    if q:
        items = items.filter(Q(sku__icontains=q) | Q(name__icontains=q) | Q(brand__icontains=q))
    if category:
        items = items.filter(category=category)
    items = list(items.distinct())
    if low == "1":
        items = [i for i in items if i.is_low_stock]
    return render(request, "inventory/partials/item_rows.html", {"items": items})


@role_required(*STOCK_ROLES)
def item_create(request):
    form = ItemForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.created_by = request.user
        item.save()
        messages.success(request, f"Item {item.sku} created.")
        return redirect("inventory:item_detail", pk=item.pk)
    return render(request, "inventory/item_form.html", {"form": form, "title": "New Item"})


@role_required(*STOCK_ROLES)
def item_edit(request, pk):
    item = get_object_or_404(Item, pk=pk)
    form = ItemForm(request.POST or None, instance=item)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Item updated.")
        return redirect("inventory:item_detail", pk=item.pk)
    return render(request, "inventory/item_form.html", {"form": form, "title": f"Edit {item.sku}"})


@role_required(*VIEW_ROLES)
def item_detail(request, pk):
    item = get_object_or_404(Item, pk=pk)
    return render(request, "inventory/item_detail.html", {"item": item, "stocks": item.stocks.select_related("warehouse").all(),
        "movements": item.movements.select_related("warehouse", "project")[:50], "adjust_form": AdjustStockForm(),
        "issue_form": IssueToProjectForm(initial={"item": item}), "can_write": request.user.can_manage_inventory})


@role_required(*STOCK_ROLES)
def adjust_stock(request, pk):
    item = get_object_or_404(Item, pk=pk)
    form = AdjustStockForm(request.POST)
    if form.is_valid():
        try:
            services.adjust_stock(item=item, warehouse=form.cleaned_data["warehouse"], quantity=form.cleaned_data["quantity"],
                user=request.user, reference=form.cleaned_data.get("reference", ""))
        except ValidationError as exc:
            return _stock_panel(request, item, error="; ".join(exc.messages))
    return _stock_panel(request, item)


@role_required(*STOCK_ROLES)
def issue_stock(request, pk):
    item = get_object_or_404(Item, pk=pk)
    form = IssueToProjectForm(request.POST)
    error = None
    if form.is_valid():
        project = Project.objects.filter(pk=request.POST.get("project")).first()
        if not project:
            error = "Select a valid project to issue to."
        else:
            try:
                services.issue_to_project(item=form.cleaned_data["item"], warehouse=form.cleaned_data["warehouse"],
                    quantity=form.cleaned_data["quantity"], project=project, user=request.user, reference=form.cleaned_data.get("reference", ""))
                messages.success(request, "Stock issued to project.")
            except services.InsufficientStock as exc:
                error = "; ".join(exc.messages)
            except ValidationError as exc:
                error = "; ".join(exc.messages)
    return _stock_panel(request, item, error=error)


def _stock_panel(request, item, error=None):
    item.refresh_from_db()
    html = render_to_string("inventory/partials/stock_panel.html", {"item": item, "stocks": item.stocks.select_related("warehouse").all(),
        "movements": item.movements.select_related("warehouse", "project")[:50], "error": error}, request=request)
    return HttpResponse(html)


@role_required(*VIEW_ROLES)
def warehouse_list(request):
    return render(request, "inventory/warehouse_list.html", {"warehouses": Warehouse.objects.all()})


@role_required(*STOCK_ROLES)
def warehouse_create(request):
    form = WarehouseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        wh = form.save(commit=False)
        wh.created_by = request.user
        wh.save()
        messages.success(request, f"Warehouse {wh.code} created.")
        return redirect("inventory:warehouse_list")
    return render(request, "inventory/simple_form.html", {"form": form, "title": "New Warehouse", "back": "inventory:warehouse_list"})


@role_required(*VIEW_ROLES)
def supplier_list(request):
    return render(request, "inventory/supplier_list.html", {"suppliers": Supplier.objects.all()})


@role_required(*PROCURE_ROLES)
def supplier_create(request):
    form = SupplierForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        s = form.save(commit=False)
        s.created_by = request.user
        s.save()
        messages.success(request, f"Supplier {s.name} created.")
        return redirect("inventory:supplier_list")
    return render(request, "inventory/simple_form.html", {"form": form, "title": "New Supplier", "back": "inventory:supplier_list"})


@role_required(*VIEW_ROLES)
def po_list(request):
    return render(request, "inventory/po_list.html", {"orders": PurchaseOrder.objects.select_related("supplier", "warehouse").all(), "statuses": POStatus.choices})


@role_required(*PROCURE_ROLES)
def po_create(request):
    po = PurchaseOrder()
    if request.method == "POST":
        form = PurchaseOrderForm(request.POST, instance=po)
        formset = POLineFormSet(request.POST, instance=po)
        if form.is_valid():
            order = form.save(commit=False)
            order.created_by = request.user
            order.save()
            formset = POLineFormSet(request.POST, instance=order)
            if formset.is_valid():
                formset.save()
            order.recalculate_total()
            messages.success(request, f"Purchase Order {order.po_number} created.")
            return redirect("inventory:po_detail", pk=order.pk)
    else:
        form = PurchaseOrderForm(instance=po)
        formset = POLineFormSet(instance=po)
    return render(request, "inventory/po_form.html", {"form": form, "formset": formset, "title": "New Purchase Order"})


@role_required(*VIEW_ROLES)
def po_detail(request, pk):
    po = get_object_or_404(PurchaseOrder.objects.select_related("supplier", "warehouse"), pk=pk)
    return render(request, "inventory/po_detail.html", {"po": po, "can_procure": request.user.can_procure})


@role_required(*PROCURE_ROLES)
def po_place(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk)
    if po.status == POStatus.DRAFT and po.lines.exists():
        po.status = POStatus.ORDERED
        po.save(update_fields=["status"])
        messages.success(request, f"PO {po.po_number} marked as Ordered.")
    return redirect("inventory:po_detail", pk=po.pk)


@role_required(*PROCURE_ROLES)
def po_receive(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk)
    if request.method == "POST" and po.status in (POStatus.ORDERED, POStatus.PARTIAL):
        received_any = False
        for line in po.lines.all():
            raw = request.POST.get(f"receive_{line.id}", "").strip()
            if not raw:
                continue
            try:
                qty = float(raw)
            except ValueError:
                continue
            if qty > 0:
                try:
                    services.receive_po_line(line=line, quantity=qty, user=request.user)
                    received_any = True
                except ValidationError as exc:
                    messages.error(request, "; ".join(exc.messages))
        if received_any:
            po.refresh_from_db()
            messages.success(request, f"Stock received into {po.warehouse.code}.")
    return redirect("inventory:po_detail", pk=po.pk)
