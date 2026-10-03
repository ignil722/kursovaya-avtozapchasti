from django.test import TestCase
from django.urls import reverse

from .models import User


class AccountTests(TestCase):
    def test_registration_always_creates_buyer(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "newbuyer",
                "first_name": "Иван",
                "last_name": "Иванов",
                "email": "buyer@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )
        self.assertRedirects(response, reverse("accounts:login"))
        user = User.objects.get(username="newbuyer")
        self.assertEqual(user.role, User.Role.BUYER)
        self.assertFalse(user.is_staff)

    def test_email_is_unique_case_insensitive_in_registration(self):
        User.objects.create_user(username="first", email="buyer@example.com", password="StrongPass123!")
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "second",
                "first_name": "Пётр",
                "last_name": "Петров",
                "email": "BUYER@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "такой почтой уже зарегистрирован")

    def test_staff_user_is_forced_to_admin_role(self):
        user = User.objects.create_user(username="staff", email="staff@example.com", password="x", is_staff=True)
        self.assertEqual(user.role, User.Role.ADMIN)

    def test_admin_can_change_login_and_stays_authenticated_after_password_change(self):
        admin = User.objects.create_user(username="admin", email="admin@example.com", password="OldAdmin123!", is_staff=True)
        self.client.force_login(admin)
        response = self.client.post(
            reverse("accounts:admin_profile"),
            {"save_profile": "1", "username": "shop-admin", "first_name": "Главный", "last_name": "Администратор", "email": "shop-admin@example.com"},
        )
        self.assertRedirects(response, reverse("accounts:admin_profile"))
        admin.refresh_from_db()
        self.assertEqual(admin.username, "shop-admin")
        response = self.client.post(
            reverse("accounts:admin_profile"),
            {"change_password": "1", "old_password": "OldAdmin123!", "new_password1": "NewAdmin456!", "new_password2": "NewAdmin456!"},
        )
        self.assertRedirects(response, reverse("accounts:admin_profile"))
        admin.refresh_from_db()
        self.assertTrue(admin.check_password("NewAdmin456!"))
        self.assertEqual(self.client.get(reverse("accounts:admin_profile")).status_code, 200)

    def test_buyer_cannot_open_admin_profile(self):
        buyer = User.objects.create_user(username="buyer2", email="buyer2@example.com", password="pass12345")
        self.client.force_login(buyer)
        self.assertEqual(self.client.get(reverse("accounts:admin_profile")).status_code, 403)
