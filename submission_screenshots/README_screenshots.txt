FloorSync — Submission Screenshots
===================================

01_login_screen.png                  - Login screen
02_register_screen.png               - Register screen (blank form)
02b_register_success_on_login.png    - Register -> redirected to Login with success banner
03_home_screen.png                   - Home screen (authenticated, "HOME SCREEN")
04_profile_screen.png                - Profile screen, saved with sample data
05_settings_screen.png               - Settings screen, saved with sample data
06_folder_structure.png              - Vertical-slicing project folder structure

NOT INCLUDED — requires your own Supabase login, so it has to be captured by you:

07_supabase_table_data.png (missing) - Screenshot of the Supabase Table Editor
    showing real rows (e.g. auth_user, profile_profile, or
    user_settings_usersettings) after you run:

        cd /home/Heron/ampparoDIR
        source .venv/bin/activate
        python manage.py migrate

    then register/log in through the app again so Supabase has real data, and
    screenshot the Table Editor at:
    https://supabase.com/dashboard/project/aefxpkndlqntqerqtvvc/editor

Notes:
- Screenshots 01-06 were captured against a temporary local SQLite database
  (this sandbox can't reach Supabase's Postgres port), purely to demonstrate
  the working UI/features. The actual submitted app is configured to use
  Supabase via .env's DATABASE_URL.
