from django.urls import path

from .api_views import EmployeeDetailView, EmployeeListCreateView

urlpatterns = [
    path("employees/", EmployeeListCreateView.as_view(), name="employee-api-list"),
    path("employees/<int:pk>/", EmployeeDetailView.as_view(), name="employee-api-detail"),
]
