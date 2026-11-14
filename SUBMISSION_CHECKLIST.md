# FloorSync Assignment: Submission & Screenshot Checklist

This checklist prepares your required screenshots and packages your code for course submission.

---

## 📸 Part 1: Required Screenshots

1. **Updated Home screen** — `http://127.0.0.1:8000/home/` while logged in.
2. **Login screen** — `http://127.0.0.1:8000/login/`.
3. **Register screen** — `http://127.0.0.1:8000/register/`.
4. **Profile screen** — `http://127.0.0.1:8000/profile/` while logged in.
5. **Settings screen** — `http://127.0.0.1:8000/settings/` while logged in.
6. **Supabase database table with data** — Supabase Dashboard → Table Editor, with a table (e.g. `auth_user` or `profile_profile`) selected and showing real rows created through the app. Do not submit an empty table or the project dashboard.
7. **Project folder structure** — showing the `apps/`, `templates/`, and `static/` vertical-slicing layout (run `python manage.py check` first to confirm everything still loads).

### Suggested walkthrough before capturing screenshots:
1. Start on `/login/`, then click through to `/register/` and back.
2. Register a new staff account (e.g. `vip_lead`) and confirm the success banner on `/login/`.
3. Log in and land on `/home/` — confirm `HOME SCREEN` and your session details render.
4. Open `/profile/`, fill in Full name / Bio, save, and confirm the success banner.
5. Open `/settings/`, toggle Dark mode / Email notifications, save, and confirm the success banner.
6. In Supabase, refresh Table Editor and confirm your user/profile/settings rows are present.

---

## 🗜️ Part 2: Packaging Your Submission ZIP

> [!IMPORTANT]
> The submission ZIP must **exclude**:
> - Virtual environment directories (`.venv`, `venv`, etc.)
> - Local SQLite database files (`db.sqlite3`, `*.db`)
> - Python compiled cache directories (`__pycache__`, `*.pyc`)
> - Your `.env` file (it holds your Supabase password) — keep `.env.example` instead

### Quick Packaging Command:
From the root of the project directory (`ampparoDIR`), run:
```bash
zip -r floorsync_submission.zip . -x ".venv/*" "venv/*" "*.sqlite3" "*.db" "__pycache__/*" "*/__pycache__/*" ".git/*" ".env"
```

### Verification Before Upload:
Inspect the generated archive to ensure no prohibited files were included:
```bash
unzip -l floorsync_submission.zip | grep -E "(\.venv|sqlite3|\.db|__pycache__|^\s*[0-9]+.*\.env$)"
```
*(This command should return **no output**, indicating a clean archive).*
