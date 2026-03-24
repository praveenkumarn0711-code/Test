from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from .models import DynamicForm


class DynamicFormApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="form_admin",
            password="FormAdminPass123!",
        )
        self.url = "/api/forms/create/"

    def test_create_requires_authentication(self):
        payload = {
            "form_name": "employee form",
            "fields": [{"label": "name", "field_type": "text", "required": True}],
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_form_normalizes_labels(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            "form_name": "employee form",
            "fields": [
                {"label": "  Full   Name  ", "field_type": "text", "required": True},
                {"label": " joining DATE ", "field_type": "date", "required": True},
            ],
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        form = DynamicForm.objects.get(pk=response.data["id"])
        labels = list(form.fields.order_by("order").values_list("label", flat=True))
        self.assertEqual(labels, ["full name", "joining date"])

    def test_create_rejects_duplicate_labels_case_insensitive(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            "form_name": "employee form",
            "fields": [
                {"label": "Name", "field_type": "text"},
                {"label": " name ", "field_type": "text"},
            ],
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("duplicate label", str(response.data.get("error", "")).lower())
