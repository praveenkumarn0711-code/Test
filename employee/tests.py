from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from forms.models import DynamicForm, FormField

from .models import Employee


class EmployeeApiTests(APITestCase):
    def setUp(self):
        self.form = DynamicForm.objects.create(name="employee form")
        FormField.objects.create(
            form=self.form,
            label="name",
            field_type="text",
            order=0,
            required=True,
        )
        FormField.objects.create(
            form=self.form,
            label="joining date",
            field_type="date",
            order=1,
            required=True,
        )
        self.list_url = "/api/employee/employees/"

    def _valid_payload(self, username="jdoe"):
        return {
            "username": username,
            "email": f"{username}@example.com",
            "first_name": "Jane",
            "last_name": "Doe",
            "password": "Str0ngPassword!123",
            "form_id": self.form.id,
            "answers": {
                "name": "Jane Doe",
                "joining date": "2026-03-24",
            },
        }

    def test_create_employee_success(self):
        response = self.client.post(self.list_url, self._valid_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Employee.objects.filter(is_deleted=False).count(), 1)
        self.assertEqual(User.objects.filter(username="jdoe").count(), 1)

    def test_create_rejects_weak_password(self):
        payload = self._valid_payload(username="weakuser")
        payload["password"] = "123"
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_list_is_paginated_and_supports_sorting(self):
        for username in ("charlie", "alice", "bob"):
            self.client.post(self.list_url, self._valid_payload(username=username), format="json")

        response = self.client.get(self.list_url + "?sort_by=username&order=asc&page_size=2")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 2)
        usernames = [item["username"] for item in response.data["results"]]
        self.assertEqual(usernames, sorted(usernames))

    def test_delete_soft_deletes_employee(self):
        create_response = self.client.post(
            self.list_url,
            self._valid_payload(username="softdel"),
            format="json",
        )
        emp_id = create_response.data["id"]

        delete_response = self.client.delete(f"/api/employee/employees/{emp_id}/")
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

        employee = Employee.objects.get(pk=emp_id)
        self.assertTrue(employee.is_deleted)
        self.assertIsNotNone(employee.deleted_at)
        self.assertTrue(User.objects.filter(username="softdel").exists())

    def test_patch_updates_answers(self):
        create_response = self.client.post(
            self.list_url,
            self._valid_payload(username="patchuser"),
            format="json",
        )
        emp_id = create_response.data["id"]

        patch_payload = {"answers": {"name": "Updated Name", "joining date": "2026-03-25"}}
        patch_response = self.client.patch(
            f"/api/employee/employees/{emp_id}/",
            patch_payload,
            format="json",
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        employee = Employee.objects.get(pk=emp_id)
        self.assertEqual(employee.form_data["name"], "Updated Name")
