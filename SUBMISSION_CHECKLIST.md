# FloorSync Assignment: Submission & Video Checklist

This checklist prepares you for recording your demo video and packaging your code for course submission.

---

## 📹 Part 1: Demo Video Flow (≤ 3 Minutes)

The assignment requires demonstrating the working authentication and navigation flow:
**`Login screen → click to Register → Register screen → transition back to Login → log in → arrive at Home screen`**

### Recommended Recording Steps:
1. **Start on Login Screen**:
   - Open your browser to `http://127.0.0.1:8000/login/`.
   - Point out the page title and branding: **"FloorSync — Staff Login"**.
   - (Optional bonus): Type invalid credentials and click *Log In* to show visible error handling (*"Invalid username or password"*).

2. **Navigate to Register**:
   - Click either the text link **`Don't have an account? Register`** or the button **`Create New Staff Account →`**.
   - Show that the browser smoothly transitions to `/register/`.

3. **Show Register Screen**:
   - Point out the page title: **"FloorSync — Staff Registration"**.
   - Point out the form fields: Username, Email, Password, and Password confirmation.
   - Click **`Already have an account? Log in`** to demonstrate bidirectional navigation back to Login.

4. **Register a New Account**:
   - Click back to `/register/`.
   - Fill in a staff username (e.g., `vip_lead`), email (`lead@floorsync.club`), and password.
   - Click **`Register Staff Account`**.
   - Show the redirect back to `/login/` with the green success notification banner (*"Account for 'vip_lead' created successfully! Please log in..."*).

5. **Log In**:
   - Enter your newly registered credentials.
   - Click **`Log In to FloorSync`**.

6. **Arrive at Home Screen**:
   - Highlight the **`HOME SCREEN`** heading rendered in the body.
   - Point out the active staff session card displaying your registered username and active tier.
   - (Optional): Click **`Log Out of Session`** to show clean session clearing back to Login.

---

## 🗜️ Part 2: Packaging Your Submission ZIP

> [!IMPORTANT]
> The submission ZIP must **exclude**:
> - Virtual environment directories (`.venv`, `venv`, etc.)
> - Local SQLite database files (`db.sqlite3`, `*.db`)
> - Python compiled cache directories (`__pycache__`, `*.pyc`)

### Quick Packaging Command:
From the root of the project directory (`ampparoDIR`), run:
```bash
zip -r floorsync_submission.zip . -x ".venv/*" "venv/*" "*.sqlite3" "*.db" "__pycache__/*" "*/__pycache__/*" ".git/*"
```

### Verification Before Upload:
Inspect the generated archive to ensure no prohibited files were included:
```bash
unzip -l floorsync_submission.zip | grep -E "(\.venv|sqlite3|\.db|__pycache__)"
```
*(This command should return **no output**, indicating a clean archive).*
