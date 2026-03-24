import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from .models import DynamicForm, FormField


def _normalize_label(raw_label):
    return " ".join(str(raw_label or "").strip().split()).lower()


@ensure_csrf_cookie
@login_required
@require_http_methods(["GET", "POST"])
def form_create_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)

        form_name = (data.get("form_name") or "").strip()
        fields_data = data.get("fields")

        if not form_name:
            return JsonResponse({"error": "Form name is required."}, status=400)
        if not isinstance(fields_data, list) or len(fields_data) == 0:
            return JsonResponse({"error": "At least one field is required."}, status=400)

        valid_types = {choice[0] for choice in FormField.FIELD_TYPES}
        normalized_labels = set()
        for i, item in enumerate(fields_data):
            if not isinstance(item, dict):
                return JsonResponse({"error": f"Field {i + 1}: invalid structure."}, status=400)
            label = _normalize_label(item.get("label"))
            field_type = item.get("field_type")
            if not label:
                return JsonResponse({"error": f"Field {i + 1}: label is required."}, status=400)
            if label in normalized_labels:
                return JsonResponse(
                    {"error": f"Field {i + 1}: duplicate label '{label}' is not allowed."},
                    status=400,
                )
            normalized_labels.add(label)
            if field_type not in valid_types:
                return JsonResponse({"error": f"Field {i + 1}: invalid field type."}, status=400)

        dynamic_form = DynamicForm.objects.create(
            name=form_name[: DynamicForm._meta.get_field("name").max_length],
        )
        max_label = FormField._meta.get_field("label").max_length
        for order, item in enumerate(fields_data):
            label = _normalize_label(item.get("label"))
            FormField.objects.create(
                form=dynamic_form,
                label=label[:max_label],
                field_type=item["field_type"],
                order=order,
            )

        return JsonResponse({"success": True, "id": dynamic_form.id})

    return render(request, "form.html")
