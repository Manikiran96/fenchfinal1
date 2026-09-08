from django import forms
from django.contrib.auth.forms import AuthenticationForm


class EmailLoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email",
        widget=forms.EmailInput(attrs={"class": "input", "autofocus": True, "placeholder": "you@company.com"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "input", "placeholder": "********"}))
