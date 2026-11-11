from django.test import TestCase
from django.urls import reverse

from accounts.models import User


class RegistrationTests(TestCase):
    def test_successful_registration(self):
        url = reverse("register")
        data = {
            "first_name": "Ali",
            "last_name": "Valiyev",
            "username": "ali_valiyev",
            "password1": "MurakkabParol_12345",
            "password2": "MurakkabParol_12345",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("profile"))

        # Foydalanuvchi yaratilganligi va tizimga kirganligi
        user = User.objects.get(username="ali_valiyev")
        self.assertEqual(user.first_name, "Ali")
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_case_insensitive_username(self):
        # Ali bo'lsa ali bilan ikkinchi marta o'tib bo'lmaydi
        User.objects.create_user(
            username="ali",
            password="Password_123",
            first_name="Ali",
            last_name="Valiyev",
        )
        url = reverse("register")
        data = {
            "first_name": "Ali2",
            "last_name": "Valiyev2",
            "username": "ALI",
            "password1": "MurakkabParol_12345",
            "password2": "MurakkabParol_12345",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)

    def test_weak_or_mismatched_password(self):
        url = reverse("register")
        # Mos kelmagan parol
        data = {
            "first_name": "Ali",
            "last_name": "Valiyev",
            "username": "ali_test",
            "password1": "MurakkabParol_12345",
            "password2": "BoshqaParol_12345",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("password2", response.context["form"].errors)

        # Zaif parol (masalan '123')
        data["password1"] = "123"
        data["password2"] = "123"
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)

    def test_empty_first_or_last_name(self):
        url = reverse("register")
        data = {
            "first_name": "",
            "last_name": "Valiyev",
            "username": "alivali",
            "password1": "MurakkabParol_12345",
            "password2": "MurakkabParol_12345",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("first_name", response.context["form"].errors)

    def test_authenticated_user_redirected_from_register(self):
        user = User.objects.create_user(
            username="testuser",
            password="Password_123",
            first_name="Test",
            last_name="User",
        )
        self.client.force_login(user)
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("profile"))

    def test_login_with_uppercase_username(self):
        # Foydalanuvchi 'ali' login bilan yaratilgan
        User.objects.create_user(
            username="ali",
            password="MurakkabParol_12345",
            first_name="Ali",
            last_name="Valiyev",
        )
        # Login formasi orqali 'Ali' deb kiritganda kirishi kerak
        response = self.client.post(
            reverse("login"),
            {"username": "Ali", "password": "MurakkabParol_12345"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("profile"))
