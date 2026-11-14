# FloorSync — Vertical Slicing + Supabase (Assignment Deliverable)

Welcome to **FloorSync**, a live floor-plan and table-status tool for nightlife venues (bridging guests and staff via real-time VIP/Regular table status with a gated staff auth system).

This deliverable follows the course's **vertical slicing** architecture: every business capability (Login, Register, Home, Profile, Settings) is its own Django app under `apps/`, owning its views, templates, and static assets. The database is Supabase PostgreSQL, configured through `DATABASE_URL`.

---

## 🗂️ Project Structure

```
apps/                  # one Django app per feature (vertical slice)
  login/  register/  home/  profile/  user_settings/
templates/              # templates/<feature>/*.html
static/
  css/<feature>/        js/<feature>/        images/<feature>/
floorsync_project/       # project config (settings.py, urls.py)
```

Each feature app owns its own `views.py`, `urls.py`, `models.py`, and (where relevant) `forms.py`/`admin.py`. `templates/base.html` is the one shared, cross-cutting layout.

---

## 🚀 Quickstart Guide

### 1. Environment Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure the database
Copy `.env.example` to `.env` and fill in your Supabase connection string (from Supabase Dashboard → Connect → Session Pooler):
```bash
cp .env.example .env
```
If `DATABASE_URL` is left unset, the project falls back to local SQLite automatically.

### 4. Run Database Migrations
```bash
python manage.py check
python manage.py makemigrations
python manage.py migrate
```

### 5. Start the Development Server
```bash
python manage.py runserver
```
Navigate to **`http://127.0.0.1:8000/`** (or `http://localhost:8000/`) in your web browser.

---

## 🧭 Application Navigation & URL Map

| Route | URL name | Description | Access |
|---|---|---|---|
| `/` | `root` | Root entrypoint; redirects authenticated users to `/home/` and unauthenticated users to `/login/` | Public |
| `/login/` | `login:login` | **FloorSync — Staff Login**: Django auth login form; includes visible error handling and navigation link to `/register/` | Public |
| `/register/` | `register:register` | **FloorSync — Staff Registration**: Staff signup (username, email, password, confirm); redirects to `/login/` upon success with flash notice | Public |
| `/home/` | `home:home` | **Home Screen**: Protected terminal landing page displaying `"HOME SCREEN"`, user session details, and quick links to Profile/Settings | Authenticated staff only |
| `/profile/` | `profile:profile` | **Profile**: View/update full name, bio, and profile photo | Authenticated staff only |
| `/settings/` | `user_settings:settings` | **Settings**: Toggle dark mode and email notification preferences | Authenticated staff only |
| `/logout/` | `logout` | Clears user session and redirects back to `/login/` with logout confirmation | Authenticated |

---

## 🧪 Automated Testing

A test suite (one `tests.py` per feature app) covers authentication, navigation, and the Profile/Settings database operations:
```bash
python manage.py test apps -v 2
```

### Test Coverage Includes:
- Root URL redirect behavior (anonymous → login, authenticated → home).
- Login page rendering, bad-credential rejection, successful login redirect.
- Registration page rendering, user creation, password-mismatch validation.
- Protection of `/home/`, `/profile/`, and `/settings/` via `@login_required`.
- Home screen rendering `"HOME SCREEN"` and authenticated username.
- Profile and Settings updates persisting to the database.
- Logout session clearing and redirect back to login.

---

## 🐘 Supabase Verification

After running `migrate` against your Supabase `DATABASE_URL`, open the Supabase Dashboard → **Table Editor** and confirm `auth_user`, `profile_profile`, and `user_settings_usersettings` tables exist and contain rows created through the app (register a user, then update their Profile/Settings screens).

---

## 📦 Submission & Demo Checklist

See [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md) for the required screenshots and packaging instructions.
