from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from .forms import EmailLoginForm
from .models import LoginAudit


def _client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    return xff.split(",")[0] if xff else request.META.get("REMOTE_ADDR")


class ERPLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailLoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        LoginAudit.objects.create(user=form.get_user(), email_attempted=form.cleaned_data.get("username", ""),
            ip_address=_client_ip(self.request), user_agent=self.request.META.get("HTTP_USER_AGENT", "")[:255], success=True)
        return response

    def form_invalid(self, form):
        LoginAudit.objects.create(email_attempted=form.cleaned_data.get("username", ""),
            ip_address=_client_ip(self.request), user_agent=self.request.META.get("HTTP_USER_AGENT", "")[:255], success=False)
        return super().form_invalid(form)


def logout_view(request):
    logout(request)
    return redirect("accounts:login")
