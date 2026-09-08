"""Project service layer. Enforces: project only after advance payment."""
from decimal import Decimal
from django.core.exceptions import ValidationError
from .models import Project, ProjectStage, ProjectMilestone


class AdvancePaymentRequired(ValidationError):
    pass


def create_project(*, customer, advance_amount, project_value, user, quotation=None, **extra):
    advance = Decimal(str(advance_amount or "0"))
    if advance <= 0:
        raise AdvancePaymentRequired("A project can only be created after an advance payment is received.")
    project = Project(customer=customer, quotation=quotation, project_value=Decimal(str(project_value or "0")),
                      advance_amount=advance, created_by=user, stage=ProjectStage.REGISTERED, **extra)
    if not project.project_manager:
        project.project_manager = user
    project.save()
    ProjectMilestone.objects.create(project=project, stage=ProjectStage.REGISTERED, title="Project registered",
                                    note=f"Advance of Rs {advance:,.2f} received.", is_done=True, created_by=user)
    return project


def build_initial_from_quotation(quotation):
    if quotation is None:
        return {}
    return {"capacity_kw": quotation.capacity_kw, "project_value": quotation.final_price + quotation.subsidy_amount, "subsidy_amount": quotation.subsidy_amount}
