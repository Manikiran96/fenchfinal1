"""Customer service layer (reused by CRM signal, API, imports)."""
from .models import Customer


def create_customer_from_lead(lead):
    existing = Customer.objects.filter(source_lead=lead).first()
    if existing:
        return existing
    return Customer.objects.create(name=lead.customer_name, phone=lead.mobile, email=lead.email,
        address=lead.address, state=lead.state, district=lead.district, city=lead.city, pincode=lead.pincode,
        source_lead=lead, account_manager=lead.assigned_to, created_by=lead.assigned_to)
