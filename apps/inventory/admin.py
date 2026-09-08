from django.contrib import admin
from .models import Warehouse, Supplier, Item, Stock, StockMovement, PurchaseOrder, PurchaseOrderLine


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "category", "brand", "unit_price", "total_stock", "reorder_level", "is_low_stock", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("sku", "name", "brand")


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ("item", "warehouse", "quantity")
    list_filter = ("warehouse",)
    search_fields = ("item__sku", "item__name")


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("created_at", "item", "warehouse", "movement_type", "quantity", "balance_after", "project", "reference")
    list_filter = ("movement_type", "warehouse")
    search_fields = ("item__sku", "reference")


class POLineInline(admin.TabularInline):
    model = PurchaseOrderLine
    extra = 0
    readonly_fields = ("amount",)


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ("po_number", "supplier", "warehouse", "status", "total_amount", "amount_paid", "created_at")
    list_filter = ("status", "warehouse")
    search_fields = ("po_number", "supplier__name")
    inlines = [POLineInline]


admin.site.register(Warehouse)
admin.site.register(Supplier)
admin.site.register(PurchaseOrderLine)
