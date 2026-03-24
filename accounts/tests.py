from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase


class AccountsAuthTests(APITestCase):
    def setUp(self):
        self.username = "auth_user"
        self.password = "StrongAuthPass123!"
        self.user = User.objects.create_user(
            username=self.username,
            password=self.password,
            email="auth@example.com",
        )

    def test_login_returns_access_and_refresh(self):
        response = self.client.post(
            "/api/accounts/login/",
            {"username": self.username, "password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
