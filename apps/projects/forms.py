from apps.quotations.models import Quotation, QuotationStatus
from django import forms

from .models import Project, ProjectDocument, ProjectMilestone, ProjectPayment

INPUT = "input"


def _style(form):
    for f in form.fields.values():
        w = f.widget
        if isinstance(w, forms.CheckboxInput):
            continue
        css = w.attrs.get("class", "")
        w.attrs["class"] = (css + " " + INPUT).strip()


class ProjectCreateForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["customer", "quotation", "project_type", "category", "capacity_kw", "project_value", "subsidy_amount", "advance_amount",
                  "location", "latitude", "longitude", "project_manager", "expected_completion"]
        widgets = {"expected_completion": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["quotation"].queryset = Quotation.objects.filter(status__in=[QuotationStatus.APPROVED, QuotationStatus.SENT])
        self.fields["quotation"].required = False
        self.fields["advance_amount"].required = True
        _style(self)

    def clean_advance_amount(self):
        amt = self.cleaned_data.get("advance_amount") or 0
        if amt <= 0:
            raise forms.ValidationError("Advance amount must be greater than 0 — a project can only be created after an advance payment.")
        return amt


class ProjectUpdateForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["project_type", "category", "capacity_kw", "project_value", "subsidy_amount", "advance_amount",
                  "location", "latitude", "longitude", "stage", "project_manager", "expected_completion", "commissioned_on"]
        widgets = {"expected_completion": forms.DateInput(attrs={"type": "date"}), "commissioned_on": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self)


class MilestoneForm(forms.ModelForm):
    class Meta:
        model = ProjectMilestone
        fields = ["stage", "title", "note", "is_done", "done_on"]
        widgets = {"note": forms.Textarea(attrs={"rows": 2}), "done_on": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self)


class PaymentForm(forms.ModelForm):
    class Meta:
        model = ProjectPayment
        fields = ["amount", "mode", "reference", "paid_on"]
        widgets = {"paid_on": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style(self)

class ProjectDocumentForm(forms.ModelForm):
    class Meta:
        model = ProjectDocument
        fields = ["category", "title", "file"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            css = f.widget.attrs.get("class", "")
            f.widget.attrs["class"] = (css + " input").strip()