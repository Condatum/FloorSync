from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse


class LoginFeatureTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.test_username = "floor_manager"
        self.test_password = "ComplexPassword123!"
        self.user = User.objects.create_user(
            username=self.test_username,
            email="manager@floorsync.club",
            password=self.test_password,
        )

    def test_login_page_loads_and_has_links(self):
        response = self.client.get(reverse('login:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login/login.html')
        self.assertTemplateUsed(response, 'base.html')
        self.assertContains(response, "FloorSync — Staff Login")
        self.assertContains(response, reverse('register:register'))

    def test_login_rejects_bad_credentials_with_visible_error(self):
        response = self.client.post(reverse('login:login'), {
            'username': self.test_username,
            'password': 'WrongPassword999!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login/login.html')
        self.assertContains(response, "Invalid username or password")
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_login_success_redirects_to_home(self):
        response = self.client.post(reverse('login:login'), {
            'username': self.test_username,
            'password': self.test_password,
        }, follow=True)
        self.assertRedirects(response, reverse('home:home'))
        self.assertContains(response, "HOME SCREEN")
        self.assertContains(response, self.test_username)

    def test_logout_clears_session_and_redirects(self):
        self.client.login(username=self.test_username, password=self.test_password)
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login:login'))

        home_response = self.client.get(reverse('home:home'))
        self.assertRedirects(home_response, f"{reverse('login:login')}?next={reverse('home:home')}")
