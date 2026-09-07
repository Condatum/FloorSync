from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User


class FloorSyncAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.test_username = "floor_manager"
        self.test_email = "manager@floorsync.club"
        self.test_password = "ComplexPassword123!"
        self.user = User.objects.create_user(
            username=self.test_username,
            email=self.test_email,
            password=self.test_password,
        )

    def test_root_redirect_anonymous(self):
        """Root URL redirects anonymous users to login."""
        response = self.client.get(reverse('root'))
        self.assertRedirects(response, reverse('login'))

    def test_root_redirect_authenticated(self):
        """Root URL redirects logged-in users to home."""
        self.client.login(username=self.test_username, password=self.test_password)
        response = self.client.get(reverse('root'))
        self.assertRedirects(response, reverse('home'))

    def test_login_page_loads_and_has_links(self):
        """Login page loads with 200, title, and link to register."""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')
        self.assertTemplateUsed(response, 'base.html')
        self.assertContains(response, "FloorSync — Staff Login")
        self.assertContains(response, reverse('register'))
        self.assertContains(response, "Don't have an account? Register")

    def test_login_rejects_bad_credentials_with_visible_error(self):
        """Login with bad credentials stays on login page and shows visible error."""
        response = self.client.post(reverse('login'), {
            'username': self.test_username,
            'password': 'WrongPassword999!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')
        self.assertContains(response, "Invalid username or password")
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_login_success_redirects_to_home(self):
        """Login with valid credentials redirects to home and authenticates user."""
        response = self.client.post(reverse('login'), {
            'username': self.test_username,
            'password': self.test_password,
        }, follow=True)
        self.assertRedirects(response, reverse('home'))
        self.assertContains(response, "HOME SCREEN")
        self.assertContains(response, self.test_username)

    def test_register_page_loads_and_has_links(self):
        """Register page loads with 200, title, and link back to login."""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')
        self.assertContains(response, "FloorSync — Staff Registration")
        self.assertContains(response, reverse('login'))
        self.assertContains(response, "Already have an account? Log in")

    def test_register_creates_user_and_redirects_to_login(self):
        """Register creates new user in database and redirects to login."""
        new_username = "vip_host"
        new_email = "host@floorsync.club"
        new_password = "SecurePassword456!"

        response = self.client.post(reverse('register'), {
            'username': new_username,
            'email': new_email,
            'password1': new_password,
            'password2': new_password,
        })
        self.assertRedirects(response, reverse('login'))

        # Verify user exists in database
        self.assertTrue(User.objects.filter(username=new_username).exists())
        created_user = User.objects.get(username=new_username)
        self.assertEqual(created_user.email, new_email)

        # Verify newly created user can log in and reach Home
        login_response = self.client.post(reverse('login'), {
            'username': new_username,
            'password': new_password,
        }, follow=True)
        self.assertRedirects(login_response, reverse('home'))
        self.assertContains(login_response, "HOME SCREEN")
        self.assertContains(login_response, new_username)

    def test_register_rejects_mismatched_passwords(self):
        """Register fails if passwords do not match."""
        initial_count = User.objects.count()
        response = self.client.post(reverse('register'), {
            'username': 'mismatched_user',
            'email': 'mismatch@floorsync.club',
            'password1': 'Password123!',
            'password2': 'DifferentPassword456!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), initial_count)
        self.assertContains(response, "The two password fields didn’t match")

    def test_home_page_blocked_for_anonymous_users(self):
        """Anonymous access to /home/ is blocked and redirects to /login/?next=/home/."""
        response = self.client.get(reverse('home'))
        expected_redirect = f"{reverse('login')}?next={reverse('home')}"
        self.assertRedirects(response, expected_redirect)

    def test_home_page_renders_home_screen_text(self):
        """Authenticated access to /home/ renders HOME SCREEN as requested."""
        self.client.login(username=self.test_username, password=self.test_password)
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/home.html')
        self.assertContains(response, "HOME SCREEN")
        self.assertContains(response, self.test_username)

    def test_logout_clears_session_and_redirects(self):
        """Logout clears the session and redirects to login."""
        self.client.login(username=self.test_username, password=self.test_password)
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))

        # Subsequent visit to /home/ should now redirect to login
        home_response = self.client.get(reverse('home'))
        self.assertRedirects(home_response, f"{reverse('login')}?next={reverse('home')}")
