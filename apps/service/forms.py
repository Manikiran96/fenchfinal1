from django import forms
from apps.accounts.models import User, Role
from apps.projects.models import Project
from .models import Technician, ServiceTicket, TicketStatus, AMCContract

INPUT = "input"


def _style(form):
    for f in form.fields.values():
        w = f.widget
        if isinstance(w, forms.CheckboxInput):
            continue
        css = w.attrs.get("class", "")
        w.attrs["class"] = (css + " " + INPUT).strip()


class TechnicianForm(forms.ModelForm):
    class Meta:
        model = Technician
        fields = ["user", "employee_code", "phone", "skills", "is_available"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].queryset = User.objects.filter(role__in=[Role.TECHNICIAN, Role.SERVICE_ENGINEER])
        _style(self)


class TicketForm(forms.ModelForm):
    class Meta:
        model = ServiceTicket
        fields = ["customer", "project", "title", "description", "category", "priority"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["project"].required = False
        self.fields["project"].queryset = Project.objects.all()
        _style(self)


class AssignForm(forms.Form):
    technician = forms.ModelChoiceField(queryset=Technician.objects.filter(is_available=True))
    note = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Assignment note (optional)..."}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs); _style(self)


class StatusForm(forms.Form):
    new_status = forms.ChoiceField(choices=TicketStatus.choices)
    resolution = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Resolution / note..."}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs); _style(self)


class UpdateForm(forms.Form):
    note = forms.CharField(widget=forms.Textarea(attrs={"rows": 2, "class": INPUT, "placeholder": "Add a comment to the ticket..."}))


class AMCForm(forms.ModelForm):
    class Meta:
        model = AMCContract
        fields = ["customer", "project", "start_date", "end_date", "amount", "visits_per_year", "notes"]
        widgets = {"start_date": forms.DateInput(attrs={"type": "date"}), "end_date": forms.DateInput(attrs={"type": "date"}), "notes": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["project"].required = False
        _style(self)


class VisitCompleteForm(forms.Form):
    technician = forms.ModelChoiceField(queryset=Technician.objects.all(), required=False)
    remarks = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Visit remarks..."}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs); _style(self)
