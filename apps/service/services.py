"""Service module business logic: ticket transitions + AMC visit scheduling."""
from datetime import timedelta
from django.utils import timezone
from .models import ServiceTicket, TicketUpdate, TicketStatus, AMCContract, AMCVisit


def assign_ticket(ticket, technician, user=None, note=""):
    old = ticket.status
    ticket.assigned_to = technician
    if ticket.status == TicketStatus.OPEN:
        ticket.status = TicketStatus.ASSIGNED
    ticket.save(update_fields=["assigned_to", "status"])
    TicketUpdate.objects.create(ticket=ticket, note=note or f"Assigned to {technician.display_name}.",
                                old_status=old, new_status=ticket.status, created_by=user)
    return ticket


def change_status(ticket, new_status, user=None, note="", resolution=""):
    old = ticket.status
    ticket.status = new_status
    fields = ["status"]
    if new_status == TicketStatus.RESOLVED:
        ticket.resolved_at = timezone.now()
        fields.append("resolved_at")
        if resolution:
            ticket.resolution = resolution
            fields.append("resolution")
    ticket.save(update_fields=fields)
    TicketUpdate.objects.create(ticket=ticket, note=note or f"Status changed {old} to {new_status}.",
                                old_status=old, new_status=new_status, created_by=user)
    return ticket


def add_update(ticket, note, user=None):
    return TicketUpdate.objects.create(ticket=ticket, note=note, created_by=user)


def generate_amc_visits(amc, user=None):
    existing = amc.visits.count()
    total_days = max((amc.end_date - amc.start_date).days, 1)
    years = max(total_days / 365.0, 1.0)
    target = max(int(round(amc.visits_per_year * years)), 1)
    to_create = target - existing
    if to_create <= 0:
        return []
    interval = total_days / target
    created = []
    for i in range(existing, target):
        day_offset = int(round(interval * (i + 1)))
        sched = amc.start_date + timedelta(days=min(day_offset, total_days))
        created.append(AMCVisit.objects.create(amc=amc, scheduled_date=sched, created_by=user))
    return created


def complete_visit(visit, user=None, remarks="", technician=None):
    visit.is_done = True
    visit.done_on = timezone.now().date()
    if remarks:
        visit.remarks = remarks
    if technician:
        visit.technician = technician
    visit.save(update_fields=["is_done", "done_on", "remarks", "technician"])
    return visit
