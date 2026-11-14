from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .models import Profile


class ProfileFeatureTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.test_username = "floor_manager"
        self.test_password = "ComplexPassword123!"
        self.user = User.objects.create_user(
            username=self.test_username,
            password=self.test_password,
        )

    def test_profile_requires_login(self):
        response = self.client.get(reverse('profile:profile'))
        self.assertRedirects(response, f"{reverse('login:login')}?next={reverse('profile:profile')}")

    def test_profile_page_loads_for_authenticated_user(self):
        self.client.login(username=self.test_username, password=self.test_password)
        response = self.client.get(reverse('profile:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile/profile.html')
        self.assertContains(response, self.test_username)

    def test_profile_update_persists_to_database(self):
        self.client.login(username=self.test_username, password=self.test_password)
        response = self.client.post(reverse('profile:profile'), {
            'full_name': 'Jordan Reyes',
            'bio': 'Floor manager on weekend shifts.',
        })
        self.assertRedirects(response, reverse('profile:profile'))

        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.full_name, 'Jordan Reyes')
        self.assertEqual(profile.bio, 'Floor manager on weekend shifts.')
