from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse


class HomeFeatureTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.test_username = "floor_manager"
        self.test_password = "ComplexPassword123!"
        self.user = User.objects.create_user(
            username=self.test_username,
            email="manager@floorsync.club",
            password=self.test_password,
        )

    def test_root_redirect_anonymous(self):
        response = self.client.get(reverse('root'))
        self.assertRedirects(response, reverse('login:login'))

    def test_root_redirect_authenticated(self):
        self.client.login(username=self.test_username, password=self.test_password)
        response = self.client.get(reverse('root'))
        self.assertRedirects(response, reverse('home:home'))

    def test_home_page_blocked_for_anonymous_users(self):
        response = self.client.get(reverse('home:home'))
        expected_redirect = f"{reverse('login:login')}?next={reverse('home:home')}"
        self.assertRedirects(response, expected_redirect)

    def test_home_page_renders_home_screen_text(self):
        self.client.login(username=self.test_username, password=self.test_password)
        response = self.client.get(reverse('home:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/home.html')
        self.assertContains(response, "HOME SCREEN")
        self.assertContains(response, self.test_username)
        self.assertContains(response, reverse('profile:profile'))
        self.assertContains(response, reverse('user_settings:settings'))
