from django import forms
from django.forms import inlineformset_factory
from .models import Quotation, QuotationItem

INPUT = "input"


def _style(form):
    for f in form.fields.values():
        css = f.widget.attrs.get("class", "")
        f.widget.attrs["class"] = (css + " " + INPUT).strip()


class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = ["capacity_kw", "panel_brand", "inverter_brand", "material_cost", "tax_percent", "subsidy_amount", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self)


class QuotationItemForm(forms.ModelForm):
    class Meta:
        model = QuotationItem
        fields = ["description", "quantity", "unit_price"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self)


QuotationItemFormSet = inlineformset_factory(Quotation, QuotationItem, form=QuotationItemForm, extra=3, can_delete=True)


class RejectForm(forms.Form):
    reason = forms.CharField(widget=forms.Textarea(attrs={"rows": 2, "class": INPUT, "placeholder": "Reason for rejection..."}), required=False)


class SendForm(forms.Form):
    to_email = forms.EmailField(widget=forms.EmailInput(attrs={"class": INPUT, "placeholder": "customer@email.com"}))
    message = forms.CharField(widget=forms.Textarea(attrs={"rows": 2, "class": INPUT, "placeholder": "Optional message..."}), required=False)
