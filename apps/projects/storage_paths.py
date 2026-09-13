"""
Central file-storage layout for the ERP.

Everything belonging to a project lands inside ONE folder on disk:

    media/projects/PRJ20260001/
        ├── documents/     ← agreements, designs, approvals, invoices
        ├── payments/      ← payment receipts / proof
        ├── site_photos/   ← technician stage photos
        └── tickets/
            └── TKT20260001/   ← service ticket photos

So opening media/projects/PRJ20260001/ shows the complete file history
of that project in one place.
"""
import os
import re


def _safe(value, fallback="unfiled"):
    """Make a filesystem-safe folder name."""
    value = str(value or "").strip()
    value = re.sub(r"[^A-Za-z0-9._-]", "_", value)
    return value or fallback


def project_root(project):
    """Base folder for a project, e.g. 'projects/PRJ20260001'."""
    return f"projects/{_safe(getattr(project, 'project_number', None))}"


# --------------------------------------------------------------------------
# upload_to callables — pass these to FileField/ImageField
# --------------------------------------------------------------------------
def project_document_path(instance, filename):
    """apps.projects.ProjectDocument.file"""
    return os.path.join(project_root(instance.project), "documents", _safe(filename))


def payment_receipt_path(instance, filename):
    """apps.projects.ProjectPayment.receipt"""
    return os.path.join(project_root(instance.project), "payments", _safe(filename))


def stage_photo_path(instance, filename):
    """apps.portal.StagePhoto.image (technician site photos)"""
    project = instance.stage_update.project
    return os.path.join(project_root(project), "site_photos", _safe(filename))


def ticket_photo_path(instance, filename):
    """apps.service.TicketPhoto.image

    Filed under the project when the ticket is linked to one, otherwise
    under a standalone tickets/ folder.
    """
    ticket = instance.ticket_update.ticket
    ticket_no = _safe(getattr(ticket, "ticket_number", None), "ticket")
    if ticket.project_id:
        return os.path.join(project_root(ticket.project), "tickets", ticket_no, _safe(filename))
    return os.path.join("tickets", ticket_no, _safe(filename))
