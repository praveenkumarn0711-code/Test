from django.db import models
from django.contrib.auth.models import User

# Create your models here.



class DynamicForm(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name


class FormField(models.Model):
    FIELD_TYPES = (
        ('text', 'Text'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('password', 'Password'),
    )

    form = models.ForeignKey(DynamicForm, related_name="fields", on_delete=models.CASCADE)
    label = models.CharField(max_length=100)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    order = models.IntegerField()
    required = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.label} ({self.field_type})"