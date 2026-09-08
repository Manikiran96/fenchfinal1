"""Customer Management views (Module 4) — HTMX CRUD + docs + notes."""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.db.models import Q
from apps.accounts.permissions import role_required
from apps.accounts.models import Role
from .models import Customer, CustomerDocument
from .forms import CustomerForm, CustomerDocumentForm, CustomerNoteForm

CUSTOMER_ROLES = (Role.SUPER_ADMIN, Role.ADMIN, Role.BRANCH_MANAGER, Role.SALES_MANAGER,
                  Role.SALES_EXECUTIVE, Role.PROJECT_MANAGER, Role.ACCOUNTS, Role.SERVICE_ENGINEER)


def _visible_customers(user):
    qs = Customer.objects.select_related("account_manager", "source_lead")
    if user.role == Role.SALES_EXECUTIVE:
        qs = qs.filter(account_manager=user)
    return qs


@role_required(*CUSTOMER_ROLES)
def customer_list(request):
    return render(request, "customers/customer_list.html", {"customers": _visible_customers(request.user)})


@role_required(*CUSTOMER_ROLES)
def customer_rows(request):
    customers = _visible_customers(request.user)
    q = request.GET.get("q", "").strip()
    if q:
        customers = customers.filter(Q(customer_code__icontains=q) | Q(name__icontains=q) | Q(phone__icontains=q) | Q(city__icontains=q))
    return render(request, "customers/partials/customer_rows.html", {"customers": customers.distinct()})


@role_required(*CUSTOMER_ROLES)
def customer_create(request):
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.created_by = request.user
            if not customer.account_manager:
                customer.account_manager = request.user
            customer.save()
            messages.success(request, f"Customer {customer.customer_code} created.")
            return redirect("customers:customer_detail", pk=customer.pk)
    else:
        form = CustomerForm()
    return render(request, "customers/customer_form.html", {"form": form, "title": "New Customer"})


@role_required(*CUSTOMER_ROLES)
def customer_edit(request, pk):
    customer = get_object_or_404(_visible_customers(request.user), pk=pk)
    form = CustomerForm(request.POST or None, instance=customer)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Customer updated.")
        return redirect("customers:customer_detail", pk=customer.pk)
    return render(request, "customers/customer_form.html", {"form": form, "title": f"Edit {customer.customer_code}"})


@role_required(*CUSTOMER_ROLES)
def customer_detail(request, pk):
    customer = get_object_or_404(_visible_customers(request.user), pk=pk)
    return render(request, "customers/customer_detail.html", {
        "customer": customer, "doc_form": CustomerDocumentForm(), "note_form": CustomerNoteForm(), "projects": customer.projects.all()})


@role_required(*CUSTOMER_ROLES)
def upload_document(request, pk):
    customer = get_object_or_404(_visible_customers(request.user), pk=pk)
    form = CustomerDocumentForm(request.POST, request.FILES)
    if form.is_valid():
        doc = form.save(commit=False)
        doc.customer = customer
        doc.created_by = request.user
        doc.save()
    html = render_to_string("customers/partials/documents.html", {"customer": customer}, request=request)
    return HttpResponse(html)


@role_required(*CUSTOMER_ROLES)
def delete_document(request, doc_id):
    doc = get_object_or_404(CustomerDocument, pk=doc_id)
    customer = doc.customer
    if request.user.role == Role.SALES_EXECUTIVE and customer.account_manager_id != request.user.id:
        return HttpResponse(status=403)
    doc.file.delete(save=False)
    doc.delete()
    html = render_to_string("customers/partials/documents.html", {"customer": customer}, request=request)
    return HttpResponse(html)


@role_required(*CUSTOMER_ROLES)
def add_note(request, pk):
    customer = get_object_or_404(_visible_customers(request.user), pk=pk)
    form = CustomerNoteForm(request.POST)
    if form.is_valid():
        note = form.save(commit=False)
        note.customer = customer
        note.created_by = request.user
        note.save()
    html = render_to_string("customers/partials/notes.html", {"customer": customer}, request=request)
    return HttpResponse(html)
