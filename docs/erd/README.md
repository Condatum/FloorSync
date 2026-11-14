# FloorSync — Physical ERD

Deliverable 02 (CSIT327). Physical entity-relationship diagram for the FloorSync live
floor-plan system.

**Target DBMS:** PostgreSQL 15 (Supabase) · **15 tables** · **20 foreign keys** · crow's-foot notation · 3NF

📄 **Rendered document:** https://claude.ai/artifact/AQa9p9Dkw2XLwL3eAG3bDf
(diagram, notation legend, relationship register R1–R20, full data dictionary, design decisions)

---

## Files

| File | What it is | Render it with |
|---|---|---|
| `floorsync_erd.dbml` | DBML source — the cleanest ERD image for submission | [dbdiagram.io/d](https://dbdiagram.io/d) → paste → **Export → PNG / PDF** |
| `floorsync_erd.mmd` | Mermaid source — same diagram as the rendered document | [mermaid.live](https://mermaid.live) → paste → **Actions → PNG / SVG** |
| `floorsync_schema.sql` | The actual PostgreSQL DDL, with every CHECK and index | Supabase **SQL Editor**, then **Database → Schema Visualizer** |

All three describe the same schema. The `.sql` file is authoritative for exact types.

---

## The 15 tables

**Identity & Access** (gatekeeper registration, two-tier roles)
`auth_user` · `staff_staffaccount` · `profile_profile` · `user_settings_usersettings`

**Floor & Concierge** (spatial mapping, duty-based contact)
`venue_venue` · `venue_floorplan` · `venue_zone` · `venue_table` · `venue_perk` ·
`venue_tableperk` · `staff_contactchannel` · `staff_dutyshift`

**Transactions & Audit** (verified workflow, reservation log)
`reservations_reservation` · `reservations_tablestatuslog`

**Empirical Validation** (15-subject usability study, deliberately unrelated)
`feedback_usabilityresponse`

Table names follow Django's physical convention `<app_label>_<modelname>`, so each vertical
slice in `apps/` owns its own tables.

### Already implemented
`auth_user` (Django), `profile_profile` (`apps/profile`), `user_settings_usersettings`
(`apps/user_settings`). The remaining 12 tables are the proposed schema for the floor-plan
and admin-hub slices.

### Omitted from the diagram
Django's own framework tables — `auth_group`, `auth_permission`, `auth_user_groups`,
`django_session`, `django_migrations`, `django_admin_log`, `django_content_type` — are created
by `manage.py migrate` and do exist in Supabase. They carry no project-specific business rules,
so the ERD leaves them out for legibility. The two-tier role model lives in
`staff_staffaccount.role` instead of `auth_group`.

---

## Notation

```
||--||   exactly one to exactly one
||--o|   one to zero-or-one      (optional 1:1)
||--o{   one to zero-or-many     (optional 1:M)
||--|{   one to one-or-many      (mandatory 1:M)
}o--o{   many to many            (always resolved via a junction table)
```

The model's only many-to-many is `venue_table` ↔ `venue_perk`, resolved physically by
`venue_tableperk` with `UNIQUE (table_id, perk_id)`.

---

## Scope boundaries encoded in the schema

| Project limitation | How the schema enforces it |
|---|---|
| Off-app settlement | No payment/transaction entity exists. `deposit_amount` + `payment_verified` only *record* a human confirmation. |
| Mediated bookings | `reservations_reservation.created_by_id` is `NOT NULL` → no ownerless reservation is possible. |
| Guests are read-only | No guest account table; guest details are plain columns on the staff-authored reservation. |
| Manual persistence | No `expires_at` / auto-release column anywhere. Status changes only on a staff toggle. |
| Single-venue logic | Exactly one `venue_venue` row with `is_active = TRUE`. |
| Audit trail integrity | Every FK from `reservations_tablestatuslog` uses `ON DELETE SET NULL`, never `CASCADE`. |
| Gatekeeper registration | `auth_user.is_active` defaults to `FALSE`; only a `SUPER_ADMIN` sets `verification_status = 'APPROVED'`. |
