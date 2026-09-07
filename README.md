# FloorSync — Authentication Scaffolding (Assignment Deliverable)

Welcome to **FloorSync**, a live floor-plan and table-status tool for nightlife venues (bridging guests and staff via real-time VIP/Regular table status with a gated staff auth system).

This deliverable fulfills the course assignment by providing the core **authentication scaffolding** and UI navigation flow with three interconnected screens:
1. **Staff Login (`/login/`)**
2. **Staff Registration (`/register/`)**
3. **Home Screen (`/home/`)**

---

## 🚀 Quickstart Guide

### 1. Environment Setup
Clone or unpack the repository into your workspace, then create and activate a Python virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Database Migrations
Initialize the local SQLite database schema:
```bash
python manage.py migrate
```

### 4. Start the Development Server
```bash
python manage.py runserver
```
Navigate to **`http://127.0.0.1:8000/`** (or `http://localhost:8000/`) in your web browser.

---

## 🧭 Application Navigation & URL Map

| Route | View Name | Description | Access |
|---|---|---|---|
| `/` | `root` | Root entrypoint; redirects authenticated users to `/home/` and unauthenticated users to `/login/` | Public |
| `/login/` | `login` | **FloorSync — Staff Login**: Django auth login form; includes visible error handling and navigation link to `/register/` | Public |
| `/register/` | `register` | **FloorSync — Staff Registration**: Staff signup (username, email, password, confirm); redirects to `/login/` upon success with flash notice | Public |
| `/home/` | `home` | **Home Screen**: Protected terminal landing page displaying `"HOME SCREEN"`, user session details, and a logout button | Authenticated staff only |
| `/logout/` | `logout` | Clears user session and redirects back to `/login/` with logout confirmation | Authenticated |

---

## 🧪 Automated Testing

A test suite covers the authentication and navigation flows:
```bash
python manage.py test accounts -v 2
```

### Test Coverage Includes:
- Root URL redirect behavior (anonymous → login, authenticated → home).
- Login page rendering and presence of link to Register.
- Visible rejection of bad login credentials.
- Registration page rendering and presence of link to Login.
- Successful user registration, database record creation, and redirect to Login.
- Password mismatch validation during registration.
- Successful authentication of newly registered user redirecting to Home.
- Protection of `/home/` via `@login_required` (anonymous users redirected to `/login/?next=/home/`).
- Home screen rendering `"HOME SCREEN"` and authenticated username.
- Logout session clearing and redirect back to login.

---

## 📦 Submission & Demo Checklist

See [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md) for:
1. The demo video recording script (`Login → Register → Login → Home`).
2. Exact instructions to exclude `.venv/` and `*.sqlite3` before creating your submission ZIP archive.
