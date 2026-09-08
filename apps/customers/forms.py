from django import forms
from .models import Customer, CustomerDocument, CustomerNote

INPUT = "input"


def _style(form):
    for f in form.fields.values():
        css = f.widget.attrs.get("class", "")
        f.widget.attrs["class"] = (css + " " + INPUT).strip()


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["name", "phone", "email", "address", "state", "district", "city", "pincode", "gst", "pan", "aadhaar", "account_manager", "is_active"]
        widgets = {"address": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self)
        self.fields["is_active"].widget.attrs.pop("class", None)


class CustomerDocumentForm(forms.ModelForm):
    class Meta:
        model = CustomerDocument
        fields = ["doc_type", "label", "file"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self)


class CustomerNoteForm(forms.ModelForm):
    class Meta:
        model = CustomerNote
        fields = ["note"]
        widgets = {"note": forms.Textarea(attrs={"rows": 2, "class": INPUT, "placeholder": "Add an interaction note..."})}
