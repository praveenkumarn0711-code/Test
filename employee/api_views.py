from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Employee
from .serializers import (
    EmployeeCreateSerializer,
    EmployeeSerializer,
    EmployeeUpdateSerializer,
)


class EmployeeListCreateView(generics.ListCreateAPIView):
    """GET: list employees. POST: create employee (user + form_id + answers)."""

    queryset = Employee.objects.filter(is_deleted=False).select_related("user", "dynamic_form")
    permission_classes = [AllowAny]
    ordering_map = {
        "id": "id",
        "created_at": "created_at",
        "updated_at": "updated_at",
        "username": "user__username",
        "form_name": "dynamic_form__name",
    }

    class EmployeePagination(PageNumberPagination):
        page_size = 10
        page_size_query_param = "page_size"
        max_page_size = 100

    pagination_class = EmployeePagination

    def get_queryset(self):
        qs = super().get_queryset()
        sort_by = self.request.query_params.get("sort_by", "created_at")
        order = self.request.query_params.get("order", "desc").lower()
        sort_field = self.ordering_map.get(sort_by, "created_at")
        if order == "asc":
            return qs.order_by(sort_field)
        return qs.order_by(f"-{sort_field}")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return EmployeeCreateSerializer
        return EmployeeSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = serializer.save()
        return Response(
            EmployeeSerializer(employee, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class EmployeeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET: one employee. PUT/PATCH: update. DELETE: soft-delete employee."""

    queryset = Employee.objects.filter(is_deleted=False).select_related("user", "dynamic_form")
    permission_classes = [AllowAny]
    lookup_field = "pk"

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return EmployeeUpdateSerializer
        return EmployeeSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.method in ("PUT", "PATCH") and self.kwargs.get("pk"):
            context["employee"] = self.get_object()
        return context

    def perform_destroy(self, instance):
        from django.utils import timezone

        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save(update_fields=["is_deleted", "deleted_at", "updated_at"])
