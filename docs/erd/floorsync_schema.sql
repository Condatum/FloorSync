-- =====================================================================
-- FloorSync — Physical schema (PostgreSQL 15 / Supabase)
-- This is the DDL the ERD documents. Django's own framework tables
-- (auth_group, auth_permission, django_session, django_migrations, ...)
-- are created by `manage.py migrate` and are omitted here for clarity.
-- =====================================================================

-- ---------- 1. IDENTITY & ACCESS ------------------------------------

-- auth_user is created by django.contrib.auth; reproduced for reference.
CREATE TABLE IF NOT EXISTS auth_user (
    id           BIGSERIAL     PRIMARY KEY,
    password     VARCHAR(128)  NOT NULL,
    last_login   TIMESTAMPTZ   NULL,
    is_superuser BOOLEAN       NOT NULL DEFAULT FALSE,
    username     VARCHAR(150)  NOT NULL UNIQUE,
    first_name   VARCHAR(150)  NOT NULL DEFAULT '',
    last_name    VARCHAR(150)  NOT NULL DEFAULT '',
    email        VARCHAR(254)  NOT NULL,
    is_staff     BOOLEAN       NOT NULL DEFAULT FALSE,
    is_active    BOOLEAN       NOT NULL DEFAULT FALSE,  -- gatekeeper flag
    date_joined  TIMESTAMPTZ   NOT NULL DEFAULT now()
);

CREATE TABLE staff_staffaccount (
    id                  BIGSERIAL    PRIMARY KEY,
    user_id             BIGINT       NOT NULL UNIQUE
                                     REFERENCES auth_user(id) ON DELETE CASCADE,
    role                VARCHAR(20)  NOT NULL DEFAULT 'STAFF'
                                     CHECK (role IN ('SUPER_ADMIN','STAFF')),
    verification_status VARCHAR(20)  NOT NULL DEFAULT 'PENDING'
                                     CHECK (verification_status IN ('PENDING','APPROVED','REJECTED')),
    employee_no         VARCHAR(20)  NULL UNIQUE,
    contact_number      VARCHAR(20)  NOT NULL DEFAULT '',
    requested_at        TIMESTAMPTZ  NOT NULL DEFAULT now(),
    verified_by_id      BIGINT       NULL
                                     REFERENCES auth_user(id) ON DELETE SET NULL,
    verified_at         TIMESTAMPTZ  NULL,
    rejection_reason    VARCHAR(255) NOT NULL DEFAULT '',
    CONSTRAINT chk_staff_verified_pair
        CHECK ((verification_status = 'PENDING' AND verified_at IS NULL)
            OR (verification_status <> 'PENDING' AND verified_at IS NOT NULL))
);
CREATE INDEX idx_staff_queue    ON staff_staffaccount (verification_status, role);
CREATE INDEX idx_staff_verifier ON staff_staffaccount (verified_by_id);

CREATE TABLE profile_profile (
    id            BIGSERIAL    PRIMARY KEY,
    user_id       BIGINT       NOT NULL UNIQUE
                               REFERENCES auth_user(id) ON DELETE CASCADE,
    full_name     VARCHAR(150) NOT NULL DEFAULT '',
    bio           TEXT         NOT NULL DEFAULT '',
    profile_image VARCHAR(100) NULL
);

CREATE TABLE user_settings_usersettings (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             BIGINT    NOT NULL UNIQUE
                                  REFERENCES auth_user(id) ON DELETE CASCADE,
    dark_mode           BOOLEAN   NOT NULL DEFAULT FALSE,
    email_notifications BOOLEAN   NOT NULL DEFAULT TRUE
);

CREATE TABLE staff_contactchannel (
    id            BIGSERIAL    PRIMARY KEY,
    staff_id      BIGINT       NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    channel_type  VARCHAR(20)  NOT NULL
                               CHECK (channel_type IN ('MESSENGER','VIBER','WHATSAPP','SMS','CALL')),
    handle_or_url VARCHAR(255) NOT NULL,
    is_primary    BOOLEAN      NOT NULL DEFAULT FALSE,
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_channel_per_staff UNIQUE (staff_id, channel_type)
);

-- ---------- 2. SPATIAL MODEL ----------------------------------------

CREATE TABLE venue_venue (
    id           BIGSERIAL    PRIMARY KEY,
    name         VARCHAR(120) NOT NULL UNIQUE,
    address      VARCHAR(255) NOT NULL DEFAULT '',
    hotline      VARCHAR(20)  NOT NULL DEFAULT '',
    opening_time TIME         NULL,
    closing_time TIME         NULL,
    is_active    BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE staff_dutyshift (
    id                 BIGSERIAL   PRIMARY KEY,
    venue_id           BIGINT      NOT NULL REFERENCES venue_venue(id) ON DELETE CASCADE,
    staff_id           BIGINT      NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    contact_channel_id BIGINT      NULL REFERENCES staff_contactchannel(id) ON DELETE SET NULL,
    started_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at           TIMESTAMPTZ NULL,
    is_active          BOOLEAN     NOT NULL DEFAULT TRUE,
    CONSTRAINT chk_shift_window CHECK (ended_at IS NULL OR ended_at > started_at)
);
-- Duty-Based Contact: at most ONE admin on the floor at a time.
CREATE UNIQUE INDEX uq_one_active_shift_per_venue
    ON staff_dutyshift (venue_id) WHERE is_active;
CREATE INDEX idx_shift_staff ON staff_dutyshift (staff_id, started_at);

CREATE TABLE venue_floorplan (
    id               BIGSERIAL    PRIMARY KEY,
    venue_id         BIGINT       NOT NULL REFERENCES venue_venue(id) ON DELETE CASCADE,
    name             VARCHAR(120) NOT NULL,
    version          INTEGER      NOT NULL DEFAULT 1 CHECK (version > 0),
    background_image VARCHAR(100) NULL,
    canvas_width     INTEGER      NOT NULL DEFAULT 1200 CHECK (canvas_width  > 0),
    canvas_height    INTEGER      NOT NULL DEFAULT 800  CHECK (canvas_height > 0),
    is_published     BOOLEAN      NOT NULL DEFAULT FALSE,
    created_by_id    BIGINT       NULL REFERENCES auth_user(id) ON DELETE SET NULL,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT uq_plan_version UNIQUE (venue_id, name, version)
);
-- Only one layout may drive the public map.
CREATE UNIQUE INDEX uq_one_published_plan
    ON venue_floorplan (venue_id) WHERE is_published;

CREATE TABLE venue_zone (
    id            BIGSERIAL   PRIMARY KEY,
    floor_plan_id BIGINT      NOT NULL REFERENCES venue_floorplan(id) ON DELETE CASCADE,
    name          VARCHAR(80) NOT NULL,
    zone_type     VARCHAR(20) NOT NULL CHECK (zone_type IN ('VIP','REGULAR')),
    display_color VARCHAR(7)  NOT NULL DEFAULT '#7C3AED',
    sort_order    SMALLINT    NOT NULL DEFAULT 0,
    CONSTRAINT uq_zone_name_per_plan UNIQUE (floor_plan_id, name)
);

CREATE TABLE venue_table (
    id                   BIGSERIAL     PRIMARY KEY,
    zone_id              BIGINT        NOT NULL REFERENCES venue_zone(id) ON DELETE CASCADE,
    code                 VARCHAR(20)   NOT NULL,
    label                VARCHAR(60)   NOT NULL DEFAULT '',
    capacity             SMALLINT      NOT NULL CHECK (capacity > 0),
    min_spend            NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (min_spend >= 0),
    shape                VARCHAR(15)   NOT NULL DEFAULT 'RECT'
                                       CHECK (shape IN ('RECT','CIRCLE','BOOTH')),
    pos_x                NUMERIC(7,2)  NOT NULL,
    pos_y                NUMERIC(7,2)  NOT NULL,
    width                NUMERIC(7,2)  NOT NULL DEFAULT 80  CHECK (width  > 0),
    height               NUMERIC(7,2)  NOT NULL DEFAULT 60  CHECK (height > 0),
    rotation             SMALLINT      NOT NULL DEFAULT 0
                                       CHECK (rotation BETWEEN 0 AND 359),
    status               VARCHAR(15)   NOT NULL DEFAULT 'AVAILABLE'
                                       CHECK (status IN ('AVAILABLE','OCCUPIED','RESERVED','BLOCKED')),
    status_updated_at    TIMESTAMPTZ   NULL,
    status_updated_by_id BIGINT        NULL REFERENCES auth_user(id) ON DELETE SET NULL,
    is_visible           BOOLEAN       NOT NULL DEFAULT TRUE,
    notes                VARCHAR(255)  NOT NULL DEFAULT '',
    CONSTRAINT uq_table_code_per_zone UNIQUE (zone_id, code)
);
CREATE INDEX idx_table_status ON venue_table (status);

CREATE TABLE venue_perk (
    id          BIGSERIAL    PRIMARY KEY,
    name        VARCHAR(60)  NOT NULL UNIQUE,
    icon        VARCHAR(40)  NOT NULL DEFAULT '',
    description VARCHAR(255) NOT NULL DEFAULT ''
);

CREATE TABLE venue_tableperk (
    id       BIGSERIAL PRIMARY KEY,
    table_id BIGINT NOT NULL REFERENCES venue_table(id) ON DELETE CASCADE,
    perk_id  BIGINT NOT NULL REFERENCES venue_perk(id)  ON DELETE CASCADE,
    CONSTRAINT uq_table_perk UNIQUE (table_id, perk_id)
);

-- ---------- 3. TRANSACTIONS & AUDIT ---------------------------------

CREATE TABLE reservations_reservation (
    id               BIGSERIAL     PRIMARY KEY,
    table_id         BIGINT        NOT NULL REFERENCES venue_table(id) ON DELETE RESTRICT,
    reference_code   VARCHAR(12)   NOT NULL UNIQUE,
    guest_name       VARCHAR(120)  NOT NULL,
    guest_contact    VARCHAR(50)   NOT NULL,
    party_size       SMALLINT      NOT NULL CHECK (party_size > 0),
    reserved_for     TIMESTAMPTZ   NOT NULL,
    deposit_amount   NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (deposit_amount >= 0),
    payment_verified BOOLEAN       NOT NULL DEFAULT FALSE,
    status           VARCHAR(15)   NOT NULL DEFAULT 'HELD'
                                   CHECK (status IN ('HELD','CONFIRMED','SEATED','COMPLETED','CANCELLED','NO_SHOW')),
    created_by_id    BIGINT        NOT NULL REFERENCES auth_user(id) ON DELETE RESTRICT,
    created_at       TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ   NOT NULL DEFAULT now(),
    remarks          TEXT          NOT NULL DEFAULT '',
    -- Verified Transaction Workflow: a table is only held on a real deposit.
    CONSTRAINT chk_confirmed_requires_payment
        CHECK (status NOT IN ('CONFIRMED','SEATED','COMPLETED') OR payment_verified)
);
CREATE INDEX idx_res_table_slot ON reservations_reservation (table_id, reserved_for);
CREATE INDEX idx_res_status     ON reservations_reservation (status);

CREATE TABLE reservations_tablestatuslog (
    id              BIGSERIAL    PRIMARY KEY,
    table_id        BIGINT       NOT NULL REFERENCES venue_table(id) ON DELETE CASCADE,
    reservation_id  BIGINT       NULL REFERENCES reservations_reservation(id) ON DELETE SET NULL,
    previous_status VARCHAR(15)  NOT NULL,
    new_status      VARCHAR(15)  NOT NULL,
    changed_by_id   BIGINT       NULL REFERENCES auth_user(id) ON DELETE SET NULL,
    changed_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    source          VARCHAR(20)  NOT NULL DEFAULT 'ADMIN_HUB'
                                 CHECK (source IN ('ADMIN_HUB','LAYOUT_EDIT','SYSTEM')),
    note            VARCHAR(255) NOT NULL DEFAULT '',
    ip_address      INET         NULL,
    CONSTRAINT chk_status_actually_changed CHECK (previous_status <> new_status)
);
CREATE INDEX idx_log_table_time ON reservations_tablestatuslog (table_id, changed_at DESC);
CREATE INDEX idx_log_actor      ON reservations_tablestatuslog (changed_by_id);

-- ---------- 4. EMPIRICAL VALIDATION ---------------------------------

CREATE TABLE feedback_usabilityresponse (
    id                      BIGSERIAL    PRIMARY KEY,
    participant_code        VARCHAR(10)  NOT NULL UNIQUE,
    participant_type        VARCHAR(10)  NOT NULL CHECK (participant_type IN ('STAFF','PATRON')),
    sus_score               NUMERIC(5,2) NULL CHECK (sus_score BETWEEN 0 AND 100),
    task_completion_seconds INTEGER      NULL CHECK (task_completion_seconds >= 0),
    clarity_rating          SMALLINT     NULL CHECK (clarity_rating BETWEEN 1 AND 5),
    comments                TEXT         NOT NULL DEFAULT '',
    submitted_at            TIMESTAMPTZ  NOT NULL DEFAULT now()
);
