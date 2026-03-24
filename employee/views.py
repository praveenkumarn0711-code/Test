import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie

from forms.models import DynamicForm, FormField

from .form_utils import validate_and_clean_form_data
from .models import Employee


def _all_dynamic_field_labels():
    labels = set(FormField.objects.values_list("label", flat=True))
    for form_data in Employee.objects.filter(is_deleted=False).values_list("form_data", flat=True):
        if isinstance(form_data, dict):
            labels.update(form_data.keys())
    return sorted(labels)


@ensure_csrf_cookie
@login_required
@require_http_methods(["GET"])
def employee_list_view(request):
    field_label = (request.GET.get("field_label") or "").strip()
    field_value = (request.GET.get("field_value") or "").strip()

    employees = Employee.objects.filter(is_deleted=False).select_related("user", "dynamic_form")

    if field_label:
        employees = employees.filter(form_data__has_key=field_label)
        if field_value:
            needle = field_value.lower()
            matched_ids = []
            for emp in employees.only("id", "form_data"):
                stored = emp.form_data.get(field_label)
                if needle in str(stored if stored is not None else "").lower():
                    matched_ids.append(emp.id)
            employees = (
                Employee.objects.filter(id__in=matched_ids)
                .select_related("user", "dynamic_form")
                .order_by("-created_at")
            )
        else:
            employees = employees.order_by("-created_at")
    else:
        employees = employees.order_by("-created_at")

    return render(
        request,
        "employee/employee_list.html",
        {
            "employees": employees,
            "dynamic_field_labels": _all_dynamic_field_labels(),
            "current_field_label": field_label,
            "current_field_value": field_value,
        },
    )


@require_http_methods(["DELETE", "POST"])
@login_required
def employee_delete_view(request, pk):
    employee = get_object_or_404(Employee, pk=pk, is_deleted=False)
    employee.is_deleted = True
    employee.deleted_at = timezone.now()
    employee.save(update_fields=["is_deleted", "deleted_at", "updated_at"])
    return JsonResponse({"success": True})


@ensure_csrf_cookie
@require_http_methods(["GET"])
def employee_create_view(request):
    dynamic_forms = DynamicForm.objects.all().order_by("name")
    return render(
        request,
        "employee/employee_form.html",
        {"dynamic_forms": dynamic_forms},
    )


@require_http_methods(["GET"])
@login_required
def employee_form_fields_view(request, form_id):
    dynamic_form = get_object_or_404(DynamicForm, id=form_id)
    fields = list(
        dynamic_form.fields.order_by("order").values("label", "field_type", "required")
    )
    return JsonResponse({"fields": fields})


@require_http_methods(["POST"])
@login_required
def employee_submit_view(request):
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload."}, status=400)

    form_id = payload.get("form_id")
    answers = payload.get("answers")
    username = (payload.get("username") or "").strip()
    email = (payload.get("email") or "").strip()
    first_name = (payload.get("first_name") or "").strip()
    last_name = (payload.get("last_name") or "").strip()
    password = payload.get("password") or ""

    if not form_id:
        return JsonResponse({"error": "Form selection is required."}, status=400)
    if not isinstance(answers, dict):
        return JsonResponse({"error": "Answers must be a key/value object."}, status=400)
    if not username:
        return JsonResponse({"error": "Username is required."}, status=400)
    if not password:
        return JsonResponse({"error": "Password is required."}, status=400)
    if User.objects.filter(username=username).exists():
        return JsonResponse({"error": "This username is already taken."}, status=400)
    if email and User.objects.filter(email=email).exists():
        return JsonResponse({"error": "This email is already in use."}, status=400)
    try:
        validate_password(password)
    except DjangoValidationError as exc:
        return JsonResponse({"error": " ".join(exc.messages)}, status=400)

    dynamic_form = get_object_or_404(DynamicForm, id=form_id)
    cleaned_answers, err = validate_and_clean_form_data(dynamic_form, answers)
    if err:
        return JsonResponse({"error": err}, status=400)

    try:
        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            employee = Employee.objects.create(
                user=user,
                dynamic_form=dynamic_form,
                form_data=cleaned_answers,
            )
    except IntegrityError:
        return JsonResponse(
            {"error": "Could not create user (duplicate username or email)."},
            status=400,
        )

    return JsonResponse({"success": True, "id": employee.id})
