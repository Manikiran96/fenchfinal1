"""Quotation service layer: PDF generation, email, revisions."""
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string


def render_quotation_pdf(quotation):
    html = render_to_string("quotations/pdf.html", {"q": quotation, "items": quotation.items.all(), "company": settings.COMPANY})
    try:
        from weasyprint import HTML
    except Exception:
        return None
    try:
        return HTML(string=html).write_pdf()
    except Exception:
        return None


def email_quotation(quotation, to_email, pdf_bytes=None, extra_message=""):
    company = settings.COMPANY
    subject = f"Solar Quotation {quotation.quotation_number} - {company['name']}"
    body = (f"Dear {quotation.lead.customer_name},\n\nPlease find attached your solar quotation "
            f"{quotation.quotation_number} for a {quotation.capacity_kw} kW system.\n\n"
            f"Final price after subsidy: Rs {quotation.final_price:,.2f}\n\n{extra_message}\n\nRegards,\n{company['name']}\n{company['phone']}")
    email = EmailMessage(subject=subject, body=body, from_email=settings.DEFAULT_FROM_EMAIL, to=[to_email])
    if pdf_bytes is None:
        pdf_bytes = render_quotation_pdf(quotation)
    if pdf_bytes:
        email.attach(f"{quotation.quotation_number}.pdf", pdf_bytes, "application/pdf")
    email.send(fail_silently=False)
    quotation.mark_sent()
    return True


def create_revision(quotation, user):
    root = quotation.parent or quotation
    new_rev_number = (root.revisions.count() + 2) if root.revisions.exists() else 2
    clone = quotation.__class__.objects.create(lead=quotation.lead, parent=root, revision=new_rev_number,
        capacity_kw=quotation.capacity_kw, panel_brand=quotation.panel_brand, inverter_brand=quotation.inverter_brand,
        material_cost=quotation.material_cost, tax_percent=quotation.tax_percent, subsidy_amount=quotation.subsidy_amount, notes=quotation.notes, created_by=user)
    for item in quotation.items.all():
        clone.items.create(description=item.description, quantity=item.quantity, unit_price=item.unit_price, created_by=user)
    clone.recalculate()
    return clone
