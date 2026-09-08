# ☀️ Solar ERP — Django + HTMX (Modular Monolith)

A role-based ERP for a medium-scale Solar EPC company. Built as a **modular
monolith** (each business domain is a separate Django app) so it's easy to
learn now and split into microservices later. **All 8 modules complete.**

## Tech stack
| Layer          | Choice                                            |
|----------------|---------------------------------------------------|
| Backend        | Python + Django + Django REST Framework           |
| Frontend       | HTMX (server-rendered partials, no SPA needed)    |
| Database       | PostgreSQL                                         |
| Auth           | Session login (web) + JWT (API) + RBAC by role    |
| PDF            | WeasyPrint (HTML→PDF) + print-view fallback       |
| Deploy         | Docker + Gunicorn + Nginx (Ubuntu)                |

## Project layout
```
solar_erp/
├── config/            # settings, root urls, wsgi/asgi
├── apps/
│   ├── core/          # shared TimeStampedModel + dashboard
│   ├── accounts/      # ✅ Module 1: users, 14 roles, RBAC, audit logs
│   ├── crm/           # ✅ Module 2: leads (HTMX CRUD + timeline + WON→customer)
│   ├── quotations/    # ✅ Module 3: pricing, approval workflow, PDF, email
│   ├── customers/     # ✅ Module 4: customers, KYC, documents, notes
│   ├── projects/      # ✅ Module 5: projects (advance-first), payments, milestones, geo
│   ├── inventory/     # ✅ Module 6: warehouses, items, stock ledger, POs, issue-to-project
│   ├── service/       # ✅ Module 7: technicians, service tickets (SLA), AMC contracts
│   └── finance/       # ✅ Module 8: receivables, payables, subsidy, net-metering
├── templates/         # base.html + per-module templates
├── static/css/        # app.css
└── docker-compose.yml
```

## ✅ Module 8 — Finance (this build)
The **consolidation layer** that unifies money from every module:

- **Consolidated dashboard** (`apps/finance/services.dashboard_context`):
  - **Receivables** = outstanding project balances + AMC balances.
  - **Payables** = outstanding purchase-order balances (total − paid).
  - **Net position** = receivables − payables (headline KPI).
  - **Cash-flow snapshot** = collected (advances + subsidy + project + AMC)
    − spent (supplier payments + expenses).
  - **Subsidy pipeline** = claimed / sanctioned / disbursed / pending.
  - **Net-metering pipeline** = counts by DISCOM status.
- **Payables**: record **SupplierPayment**s against POs — each rolls up into
  `PurchaseOrder.amount_paid`, shrinking the payable balance in real time.
- **Receivables**: record **AMCPayment**s against contracts — each rolls up
  into `AMCContract.amount_paid`. (Project receivables already live on
  `Project.pending_amount` from Module 5.)
- **Expenses**: general overheads (salary, rent, transport…), auto-numbered
  `EXP20260001`, optionally tagged to a project.
- **Subsidy tracking**: `SubsidyClaim` per project with a
  **Pending → Applied → Sanctioned → Disbursed** pipeline and amounts at each
  stage; dashboard shows pending disbursement.
- **Net metering**: `NetMetering` per project tracking DISCOM application,
  consumer no, sanctioned load, and status
  (Applied → Inspection → Approved → Meter Installed → Commissioned).
- Verified end to end: receivables/payables/net-position math, supplier &
  AMC payment sync, subsidy pipeline, cash-flow rollup, and net-metering
  counts all pass an automated test. System check = 0 issues.

### How the money consolidates
```
Projects ─(pending_amount)─┐
                            ├─▶ RECEIVABLES ─┐
AMC contracts ─(balance)───┘                 ├─▶ NET POSITION (dashboard)
Purchase Orders ─(balance)──▶ PAYABLES ──────┘
Advances+Subsidy+AMC ─▶ collected ┐
Supplier payments+Expenses ─▶ spent ┴─▶ NET CASH
Subsidy claims ─▶ claimed / sanctioned / disbursed pipeline
```

## Run locally (without Docker)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # edit DB creds / SECRET_KEY
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
> **PDF note:** WeasyPrint needs Pango/Cairo native libs (already in the
> Dockerfile). Without them the quotation PDF falls back to the print view.

## Run with Docker
```bash
cp .env.example .env
docker compose up --build       # web :8000, nginx :80
```

## The HTMX pattern (learn once, reuse everywhere)
A full page renders `base.html` + a target `<div>`; controls carry
`hx-get`/`hx-post` + `hx-target`; the view returns only a partial that HTMX
swaps in — no reload, no JSON/JS glue.

## Roadmap — COMPLETE 🎉
1. ✅ User Management + RBAC (accounts)
2. ✅ CRM & Leads (crm)
3. ✅ Quotation Management — PDF + approval + email (quotations)
4. ✅ Customer Management + documents (customers)
5. ✅ Project Management — advance-first, payments, milestones, geo (projects)
6. ✅ Inventory / Procurement / Warehouse — stock ledger + POs (inventory)
7. ✅ Service — technicians, tickets (SLA), AMC contracts (service)
8. ✅ Finance — receivables, payables, subsidy, net-metering (finance)

## RBAC quick reference
```python
from apps.accounts.permissions import role_required
from apps.accounts.models import Role

@role_required(Role.ACCOUNTS, Role.ADMIN, Role.BRANCH_MANAGER)
def pay_supplier(request, po_id): ...
```
Role helpers on `User`: `can_approve_quotation`, `can_manage_projects`,
`can_manage_inventory`, `can_procure`, `can_manage_service`, `can_manage_finance`.
