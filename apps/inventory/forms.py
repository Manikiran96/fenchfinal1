from django import forms
from django.forms import inlineformset_factory
from .models import Warehouse, Supplier, Item, PurchaseOrder, PurchaseOrderLine

INPUT = "input"


def _style(form):
    for f in form.fields.values():
        w = f.widget
        if isinstance(w, forms.CheckboxInput):
            continue
        css = w.attrs.get("class", "")
        w.attrs["class"] = (css + " " + INPUT).strip()


class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = ["name", "code", "address", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs); _style(self)


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ["name", "contact_person", "phone", "email", "gst", "address", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs); _style(self)


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ["sku", "name", "category", "unit", "brand", "unit_price", "reorder_level", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs); _style(self)


class AdjustStockForm(forms.Form):
    warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.filter(is_active=True))
    quantity = forms.DecimalField(help_text="Signed: +add / -remove", max_digits=12, decimal_places=2)
    reference = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs); _style(self)


class IssueToProjectForm(forms.Form):
    item = forms.ModelChoiceField(queryset=Item.objects.filter(is_active=True))
    warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.filter(is_active=True))
    quantity = forms.DecimalField(min_value=0.01, max_digits=12, decimal_places=2)
    reference = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs); _style(self)


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ["supplier", "warehouse", "expected_date", "notes"]
        widgets = {"expected_date": forms.DateInput(attrs={"type": "date"}), "notes": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs); _style(self)


class POLineForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderLine
        fields = ["item", "quantity", "unit_price"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs); _style(self)


POLineFormSet = inlineformset_factory(PurchaseOrder, PurchaseOrderLine, form=POLineForm, extra=3, can_delete=True)
