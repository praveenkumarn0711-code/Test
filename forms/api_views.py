from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DynamicForm, FormField


class DynamicFormCreateAPIView(APIView):
 
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _normalize_label(raw_label):
        return " ".join(str(raw_label or "").strip().split()).lower()

    def post(self, request):
        form_name = (request.data.get("form_name") or "").strip()
        fields_data = request.data.get("fields")

        if not form_name:
            return Response({"error": "Form name is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(fields_data, list) or len(fields_data) == 0:
            return Response(
                {"error": "At least one field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        valid_types = {choice[0] for choice in FormField.FIELD_TYPES}
        max_name = DynamicForm._meta.get_field("name").max_length
        max_label = FormField._meta.get_field("label").max_length
        normalized_labels = set()

        for i, item in enumerate(fields_data):
            if not isinstance(item, dict):
                return Response(
                    {"error": f"Field {i + 1}: invalid structure."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            label = self._normalize_label(item.get("label"))
            field_type = item.get("field_type")
            if not label:
                return Response(
                    {"error": f"Field {i + 1}: label is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if label in normalized_labels:
                return Response(
                    {"error": f"Field {i + 1}: duplicate label '{label}' is not allowed."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            normalized_labels.add(label)
            if field_type not in valid_types:
                return Response(
                    {"error": f"Field {i + 1}: invalid field type."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        dynamic_form = DynamicForm.objects.create(name=form_name[:max_name])

        for order, item in enumerate(fields_data):
            label = self._normalize_label(item.get("label"))
            FormField.objects.create(
                form=dynamic_form,
                label=label[:max_label],
                field_type=item["field_type"],
                order=order,
                required=bool(item.get("required", False)),
            )

        return Response(
            {"success": True, "id": dynamic_form.id},
            status=status.HTTP_201_CREATED,
        )
