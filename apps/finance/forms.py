from django import forms
from apps.inventory.models import PurchaseOrder
from apps.service.models import AMCContract
from .models import (SupplierPayment, AMCPayment, Expense, SubsidyClaim, NetMetering)

INPUT = "input"


def _style(form):
    for f in form.fields.values():
        w = f.widget
        if isinstance(w, forms.CheckboxInput):
            continue
        css = w.attrs.get("class", "")
        w.attrs["class"] = (css + " " + INPUT).strip()


class SupplierPaymentForm(forms.ModelForm):
    class Meta:
        model = SupplierPayment
        fields = ["amount", "mode", "reference", "paid_on"]
        widgets = {"paid_on": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs); _style(self)


class AMCPaymentForm(forms.ModelForm):
    class Meta:
        model = AMCPayment
        fields = ["amount", "mode", "reference", "paid_on"]
        widgets = {"paid_on": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs); _style(self)


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["category", "description", "amount", "mode", "project", "spent_on"]
        widgets = {"spent_on": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["project"].required = False
        _style(self)


class SubsidyClaimForm(forms.ModelForm):
    class Meta:
        model = SubsidyClaim
        fields = ["project", "claimed_amount", "sanctioned_amount", "disbursed_amount",
                  "status", "application_no", "applied_on", "sanctioned_on", "disbursed_on", "coordinator", "notes"]
        widgets = {"applied_on": forms.DateInput(attrs={"type": "date"}),
                   "sanctioned_on": forms.DateInput(attrs={"type": "date"}),
                   "disbursed_on": forms.DateInput(attrs={"type": "date"}),
                   "notes": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["coordinator"].required = False
        _style(self)


class NetMeteringForm(forms.ModelForm):
    class Meta:
        model = NetMetering
        fields = ["project", "discom", "application_no", "consumer_no", "sanctioned_load_kw",
                  "status", "applied_on", "approved_on", "meter_installed_on", "notes"]
        widgets = {"applied_on": forms.DateInput(attrs={"type": "date"}),
                   "approved_on": forms.DateInput(attrs={"type": "date"}),
                   "meter_installed_on": forms.DateInput(attrs={"type": "date"}),
                   "notes": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs); _style(self)
