# FloorSync — Live Venue Floor Plan, Table Status & Concierge Operations

**FloorSync** is a full-stack Django web application built for real-time nightlife venue table availability, spatial floor mapping, verified staff-mediated reservations, and concierge duty routing. Designed around **vertical slicing** under `apps/` with **Supabase PostgreSQL** (`DATABASE_URL`) and automatic **SQLite** fallback, it bridges guests and venue staff with a single source of truth for floor operations.

---

## Overview & Problem Statement

In nightlife venues such as **Nocturnal Cebu**, table inquiries and VIP bookings are often coordinated across fragmented messaging threads (Messenger, Instagram DMs, WhatsApp, SMS), creating operational friction:

- **Fragmented Messaging:** Guest inquiries are scattered across personal DMs and multiple staff accounts without a centralized table availability view.
- **Response Lag:** Guests wait on manual replies to learn which VIP booths or regular tables are open, causing drop-offs during peak hours.
- **Information Asymmetry:** Guests lack visibility into zone layouts, table capacities, minimum spends, and included perks, while staff lack a shared live floor state.
- **Operational Risk:** Uncoordinated verbal or DM bookings lead to double-bookings, unverified deposit claims, and missing accountability for table status changes.

---

## Objectives

1. **Dynamic Spatial Mapping:** Provide an interactive 2D floor plan (`/floor/`) displaying zones, table coordinates, capacities, perks, and live availability (`AVAILABLE`, `RESERVED`, `OCCUPIED`, `HOLD`).
2. **Verified Transaction Workflow:** Enforce staff-mediated reservation logging (`/reservations/`) with off-app deposit tracking, payment verification flags, automatic table status synchronization, and an immutable `TableStatusLog` audit ledger (`/reservations/audit/`).
3. **Hierarchical Access Control:** Implement two-tier staff gatekeeping (`PENDING` → `APPROVED` / `REJECTED`) managed by `SUPER_ADMIN` accounts (`/staff/vetting/`), protecting operational hubs and spatial configuration (`/floor/hub/`, `/floor/manage/`).
4. **Direct Concierge Integration:** Route guest table inquiries directly to the currently on-duty concierge's active contact channel (`DutyShift` + `ContactChannel`) via deep links generated on the live floor map (`/staff/duty/`, `/floor/`).
5. **Empirical Validation:** Capture structured usability study responses and live summary metrics (`/feedback/`) to evaluate guest and staff task clarity and responsiveness.

---

## Limitations

- **Off-App Settlement:** Deposits and table minimums are settled externally (e.g., bank transfer, e-wallet, or cash) and recorded manually via `payment_verified` by approved staff.
- **Mediated Bookings:** Guests cannot self-book tables directly on the map; inquiries route to the on-duty concierge, who logs and verifies the reservation.
- **Single-Venue Logic:** Operational views, floor plans, and duty routing target a single active primary venue (`Nocturnal Cebu`) at a time.
- **Manual Persistence:** Table states do not auto-expire on timers; staff explicitly toggle table statuses in the Admin Hub or via reservation updates, with every change recorded in `TableStatusLog`.

---

## Project Structure

FloorSync uses a **vertical-slice** architecture where each business capability owns its `models.py`, `views.py`, `urls.py`, `forms.py`, `admin.py`, `tests.py`, templates, and static assets:

```text
apps/                         # Vertical-slice Django apps
  login/                      # Staff authentication (/login/, /logout/)
  register/                   # Staff registration & gatekeeper onboarding (/register/)
  home/                       # Root redirect (/) & FloorSync Command Center (/home/)
  profile/                    # Staff profile & avatar management (/profile/)
  user_settings/              # Theme & notification preferences (/settings/)
  staff/                      # Gatekeeper vetting (/staff/vetting/) & duty shifts (/staff/duty/)
  venue/                      # Interactive 2D floor map (/floor/), Admin Hub (/floor/hub/), Spatial Manager (/floor/manage/)
  reservations/               # Staff reservations (/reservations/) & status audit ledger (/reservations/audit/)
  feedback/                   # Usability study form & metrics dashboard (/feedback/)
templates/                    # Shared base.html + templates/<feature>/*.html
static/
  css/<feature>/              # Feature-scoped stylesheets
  js/<feature>/               # Feature-scoped client scripts
  images/<feature>/           # Feature-scoped image assets
floorsync_project/            # Django project configuration (settings.py, urls.py, wsgi.py)
```

---

## Quickstart Guide

### 1. Create and Activate Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure the Database
Copy `.env.example` to `.env` and set `DATABASE_URL` to your Supabase PostgreSQL connection string if using Supabase:
```bash
cp .env.example .env
```
To run locally with SQLite instead of PostgreSQL, leave `DATABASE_URL` unset or pass `DATABASE_URL=""`.

### 4. Run Migrations and Seed Venue Data
```bash
DATABASE_URL="" .venv/bin/python manage.py migrate
DATABASE_URL="" .venv/bin/python manage.py seed_venue
```
(`seed_venue` is idempotent and seeds **Nocturnal Cebu** with its `Main Floor` layout, zones, tables, and perks.)

### 5. Start the Development Server
```bash
DATABASE_URL="" .venv/bin/python manage.py runserver
```
Open **`http://127.0.0.1:8000/`** (or **`http://127.0.0.1:8000/floor/`** for the public live floor map) in your browser.

---

## Application Navigation & URL Map

| Route | URL Name | Description | Access |
|---|---|---|---|
| `/` | `root` | Root entrypoint; redirects authenticated users to `/home/` and anonymous users to `/login/` | Public |
| `/floor/` | `venue:public_map` | **Live Floor Map**: Interactive 2D venue map with zones, table statuses, perks, and on-duty concierge deep links | Public |
| `/floor/hub/` | `venue:admin_hub` | **Admin Hub**: Single-tap staff table status toggles and operational overview | Authenticated (`APPROVED` staff) |
| `/floor/manage/` | `venue:spatial_manage` | **Spatial Manager**: Create/edit zones, table coordinates, capacities, and floor plan layout | Authenticated (`SUPER_ADMIN`) |
| `/login/` | `login:login` | **Staff Login**: Credential authentication with error feedback and link to `/register/` | Public |
| `/register/` | `register:register` | **Staff Registration**: New staff signup; creates `StaffAccount` in `PENDING` gatekeeper state | Public |
| `/home/` | `home:home` | **Command Center**: Protected staff dashboard with live table counts, duty status, and module links | Authenticated |
| `/reservations/` | `reservations:list` | **Reservations**: Staff-mediated booking creation, deposit/payment verification, and table status sync | Authenticated (`APPROVED` staff) |
| `/reservations/audit/` | `reservations:audit` | **Audit Ledger**: Chronological `TableStatusLog` history of table status transitions and actors | Authenticated |
| `/staff/vetting/` | `staff:vetting` | **Staff Vetting**: Gatekeeper queue to approve or reject pending staff accounts | Authenticated (`SUPER_ADMIN`) |
| `/staff/duty/` | `staff:duty` | **Duty & Concierge**: Manage `ContactChannel` endpoints and active `DutyShift` concierge routing | Authenticated (`APPROVED` staff) |
| `/feedback/` | `feedback:study` | **Usability Study**: Empirical usability survey form and live aggregated study metrics | Public |
| `/profile/` | `profile:profile` | **Profile**: View and update full name, bio, and profile photo | Authenticated |
| `/settings/` | `user_settings:settings` | **Settings**: Toggle dark mode and email notification preferences | Authenticated |
| `/logout/` | `logout` | Clears the current user session and redirects to `/login/` | Authenticated |

---

## Automated Testing

Run the full 31-test suite across all 9 vertical-slice apps using the SQLite fallback:

```bash
DATABASE_URL="" .venv/bin/python manage.py test apps -v 2
```

### Coverage Summary (31 Tests)
- **Auth & Core (`login`, `register`, `home`, `profile`, `user_settings`):** Root redirects, login/logout session handling, registration validation, `@login_required` enforcement, Command Center metrics, and Profile/Settings persistence.
- **Venue & Spatial Map (`venue`):** Public map auto-seeding and concierge deep links, idempotent `seed_venue` command, `APPROVED` staff single-tap status toggles creating `TableStatusLog` entries, and `SUPER_ADMIN` spatial management access control.
- **Staff Gatekeeper & Duty (`staff`):** `PENDING` staff blocking vs. `SUPER_ADMIN` approval workflow, and `DutyShift` / `ContactChannel` concierge deep-link routing.
- **Reservations & Audit (`reservations`):** Gatekeeper enforcement on reservation creation, verified reservation table-status synchronization, and `TableStatusLog` audit ledger rendering.
- **Usability Study (`feedback`):** Public study page access, valid response submission with live metric updates, and duplicate participant code rejection.
