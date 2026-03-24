from datetime import date

from forms.models import DynamicForm


def validate_and_clean_form_data(dynamic_form: DynamicForm, answers: dict):
    """
    Validate answers against the form’s field definitions.

    Returns (cleaned_dict, None) on success, or (None, error_message) on failure.
    """
    if not isinstance(answers, dict):
        return None, "Answers must be a key/value object."

    cleaned = {}

    for field in dynamic_form.fields.order_by("order"):
        raw = answers.get(field.label, "")
        value = raw.strip() if isinstance(raw, str) else raw
        empty = value in (None, "")

        if field.required and empty:
            return None, f"'{field.label}' is required."
        if empty:
            cleaned[field.label] = ""
            continue

        coerced, error = _coerce_value(field.label, field.field_type, value)
        if error:
            return None, error
        cleaned[field.label] = coerced

    return cleaned, None


def _coerce_value(label: str, field_type: str, value):
    """Turn the submitted value into the type we store in JSON. Returns (value, None) or (None, error)."""
    if field_type == "number":
        try:
            return float(value), None
        except (TypeError, ValueError):
            return None, f"'{label}' must be a valid number."

    if field_type == "date":
        try:
            return date.fromisoformat(str(value)).isoformat(), None
        except ValueError:
            return None, f"'{label}' must be a valid date (YYYY-MM-DD)."

    # text, password, and anything else: store as string
    return str(value), None
