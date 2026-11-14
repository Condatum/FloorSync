from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse


class RegisterFeatureTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_register_page_loads_and_has_links(self):
        response = self.client.get(reverse('register:register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register/register.html')
        self.assertContains(response, "FloorSync — Staff Registration")
        self.assertContains(response, reverse('login:login'))

    def test_register_creates_user_and_redirects_to_login(self):
        new_username = "vip_host"
        new_email = "host@floorsync.club"
        new_password = "SecurePassword456!"

        response = self.client.post(reverse('register:register'), {
            'username': new_username,
            'email': new_email,
            'password1': new_password,
            'password2': new_password,
        })
        self.assertRedirects(response, reverse('login:login'))

        self.assertTrue(User.objects.filter(username=new_username).exists())
        created_user = User.objects.get(username=new_username)
        self.assertEqual(created_user.email, new_email)

        login_response = self.client.post(reverse('login:login'), {
            'username': new_username,
            'password': new_password,
        }, follow=True)
        self.assertRedirects(login_response, reverse('home:home'))
        self.assertContains(login_response, "HOME SCREEN")
        self.assertContains(login_response, new_username)

    def test_register_rejects_mismatched_passwords(self):
        initial_count = User.objects.count()
        response = self.client.post(reverse('register:register'), {
            'username': 'mismatched_user',
            'email': 'mismatch@floorsync.club',
            'password1': 'Password123!',
            'password2': 'DifferentPassword456!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), initial_count)
        self.assertContains(response, "The two password fields didn’t match")
