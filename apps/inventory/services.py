"""Inventory service layer — the ONLY place stock quantities change."""
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Stock, StockMovement, MovementType, POStatus


class InsufficientStock(ValidationError):
    pass


@transaction.atomic
def record_movement(*, item, warehouse, quantity, movement_type, user=None, reference="", project=None, allow_negative=False):
    qty = Decimal(str(quantity))
    if qty == 0:
        raise ValidationError("Movement quantity cannot be zero.")
    stock, _ = Stock.objects.select_for_update().get_or_create(item=item, warehouse=warehouse, defaults={"quantity": Decimal("0")})
    new_balance = stock.quantity + qty
    if new_balance < 0 and not allow_negative:
        raise InsufficientStock(f"Not enough stock of {item.sku} at {warehouse.code}: have {stock.quantity}, tried to remove {abs(qty)}.")
    stock.quantity = new_balance
    stock.save(update_fields=["quantity"])
    return StockMovement.objects.create(item=item, warehouse=warehouse, movement_type=movement_type,
        quantity=qty, balance_after=new_balance, reference=reference, project=project, created_by=user)


def stock_in(*, item, warehouse, quantity, user=None, reference=""):
    return record_movement(item=item, warehouse=warehouse, quantity=abs(Decimal(str(quantity))), movement_type=MovementType.IN, user=user, reference=reference)


def issue_to_project(*, item, warehouse, quantity, project, user=None, reference=""):
    qty = abs(Decimal(str(quantity)))
    ref = reference or f"Issued to {project.project_number}"
    return record_movement(item=item, warehouse=warehouse, quantity=-qty, movement_type=MovementType.OUT, user=user, reference=ref, project=project)


def adjust_stock(*, item, warehouse, quantity, user=None, reference=""):
    return record_movement(item=item, warehouse=warehouse, quantity=Decimal(str(quantity)), movement_type=MovementType.ADJUST, user=user, reference=reference or "Manual adjustment", allow_negative=False)


@transaction.atomic
def receive_po_line(*, line, quantity, user=None):
    qty = Decimal(str(quantity))
    if qty <= 0:
        raise ValidationError("Receive quantity must be greater than zero.")
    if qty > line.pending_qty:
        raise ValidationError(f"Cannot receive {qty}; only {line.pending_qty} pending on this line.")
    po = line.purchase_order
    stock_in(item=line.item, warehouse=po.warehouse, quantity=qty, user=user, reference=f"Receipt against {po.po_number}")
    line.received_qty = (line.received_qty or Decimal("0")) + qty
    line.save(update_fields=["received_qty"])
    if line.unit_price:
        line.item.unit_price = line.unit_price
        line.item.save(update_fields=["unit_price"])
    _refresh_po_status(po)
    return line


def _refresh_po_status(po):
    lines = list(po.lines.all())
    if lines and all(li.received_qty >= li.quantity for li in lines):
        po.status = POStatus.RECEIVED
    elif any(li.received_qty > 0 for li in lines):
        po.status = POStatus.PARTIAL
    po.save(update_fields=["status"])
