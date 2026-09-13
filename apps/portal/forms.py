from django import forms
from apps.crm.models import Lead, LeadActivity
from apps.service.models import TicketStatus
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
    """Lead capture for the mobile sales portal (incl. cost + referral)."""
    class Meta:
        model = Lead
        fields = [
            "customer_name", "mobile", "email", "city",
            "source", "expected_capacity_kw", "project_cost",
            "referred_by", "referral_name", "referral_mobile", "referral_bonus",
            "remarks",
        ]
        widgets = {"remarks": forms.Textarea(attrs={"rows": 2, "placeholder": "Any remarks..."})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self)


class FollowUpForm(forms.ModelForm):
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
    class Meta:
        model = StageUpdate
        fields = ["stage", "note", "is_done"]
        widgets = {"note": forms.Textarea(attrs={"rows": 2, "placeholder": "What did you do?"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self)


class TicketWorkForm(forms.Form):
    """Technician ticket update: status + note (+ photos handled in the view)."""
    new_status = forms.ChoiceField(choices=TicketStatus.choices, label="Status")
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": "What did you do on site?"}))
    resolution = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Resolution (if resolving)..."}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self)
