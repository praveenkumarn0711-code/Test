from django.contrib.auth.models import User
from django.db import models

from forms.models import DynamicForm


class Employee(models.Model):
    user = models.ForeignKey(
        User, related_name="employees", on_delete=models.CASCADE
    )
    dynamic_form = models.ForeignKey(
        DynamicForm, related_name="employees", on_delete=models.CASCADE
    )
    form_data = models.JSONField(default=dict)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        name = self.user.get_full_name().strip()
        return name or self.user.username
