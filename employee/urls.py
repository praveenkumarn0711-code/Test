from django.urls import path

from .views import (
    employee_create_view,
    employee_delete_view,
    employee_form_fields_view,
    employee_list_view,
    employee_submit_view,
)


urlpatterns = [
    path("list/", employee_list_view, name="employee-list"),
    path("<int:pk>/delete/", employee_delete_view, name="employee-delete"),
    path("create/", employee_create_view, name="employee-create"),
    path("forms/<int:form_id>/fields/", employee_form_fields_view, name="employee-form-fields"),
    path("submit/", employee_submit_view, name="employee-submit"),
]
