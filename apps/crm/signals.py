"""When a lead is marked WON, auto-create a Customer (idempotent)."""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Lead, LeadStatus


@receiver(post_save, sender=Lead)
def auto_convert_on_won(sender, instance, created, **kwargs):
    if instance.status == LeadStatus.WON and not instance.is_converted:
        from apps.customers.services import create_customer_from_lead
        create_customer_from_lead(instance)
        Lead.objects.filter(pk=instance.pk).update(is_converted=True)
        instance.is_converted = True
