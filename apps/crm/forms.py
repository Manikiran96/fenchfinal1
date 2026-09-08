from django import forms
from .models import Lead, LeadActivity

INPUT = "input"


class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ["customer_name", "mobile", "email", "address", "state", "district",
                  "city", "pincode", "source", "expected_capacity_kw", "expected_budget", "remarks", "status", "assigned_to"]
        widgets = {"address": forms.Textarea(attrs={"rows": 2}), "remarks": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            css = f.widget.attrs.get("class", "")
            f.widget.attrs["class"] = (css + " " + INPUT).strip()


class LeadActivityForm(forms.ModelForm):
    class Meta:
        model = LeadActivity
        fields = ["note", "next_follow_up"]
        widgets = {"note": forms.Textarea(attrs={"rows": 2, "class": INPUT, "placeholder": "Add a follow-up note..."}),
                   "next_follow_up": forms.DateInput(attrs={"type": "date", "class": INPUT})}
