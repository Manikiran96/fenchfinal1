from django import forms
from apps.crm.models import Lead, LeadActivity
from .models import StageUpdate

INPUT = "pinput"


def _style(form):
    for f in form.fields.values():
        w = f.widget
        if isinstance(w, forms.CheckboxInput):
            continue
        css = w.attrs.get("class", "")
        w.attrs["class"] = (css + " " + INPUT).strip()


class QuickLeadForm(forms.ModelForm):
    """Minimal lead-capture form for the mobile sales portal."""
    class Meta:
        model = Lead
        fields = ["customer_name", "mobile", "email", "city",
                  "source", "expected_capacity_kw", "remarks"]
        widgets = {"remarks": forms.Textarea(attrs={"rows": 2, "placeholder": "Notes..."})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self)


class FollowUpForm(forms.ModelForm):
    """Add a day-wise follow-up note to a lead."""
    class Meta:
        model = LeadActivity
        fields = ["note", "next_follow_up"]
        widgets = {
            "note": forms.Textarea(attrs={"rows": 2, "placeholder": "What happened today?"}),
            "next_follow_up": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self)


class StageUpdateForm(forms.ModelForm):
    """Technician posts a work-stage update (photos handled separately)."""
    class Meta:
        model = StageUpdate
        fields = ["stage", "note", "is_done"]
        widgets = {"note": forms.Textarea(attrs={"rows": 2, "placeholder": "What did you do?"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self)
