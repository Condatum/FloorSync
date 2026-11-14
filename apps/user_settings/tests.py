from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .models import UserSettings


class UserSettingsFeatureTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.test_username = "floor_manager"
        self.test_password = "ComplexPassword123!"
        self.user = User.objects.create_user(
            username=self.test_username,
            password=self.test_password,
        )

    def test_settings_requires_login(self):
        response = self.client.get(reverse('user_settings:settings'))
        self.assertRedirects(response, f"{reverse('login:login')}?next={reverse('user_settings:settings')}")

    def test_settings_page_loads_for_authenticated_user(self):
        self.client.login(username=self.test_username, password=self.test_password)
        response = self.client.get(reverse('user_settings:settings'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_settings/settings.html')

    def test_settings_update_persists_to_database(self):
        self.client.login(username=self.test_username, password=self.test_password)
        response = self.client.post(reverse('user_settings:settings'), {
            'dark_mode': 'on',
        })
        self.assertRedirects(response, reverse('user_settings:settings'))

        settings_obj = UserSettings.objects.get(user=self.user)
        self.assertTrue(settings_obj.dark_mode)
        self.assertFalse(settings_obj.email_notifications)
