from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers

from forms.models import DynamicForm

from .form_utils import validate_and_clean_form_data
from .models import Employee


class EmployeeSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    dynamic_form_id = serializers.IntegerField(source="dynamic_form.id", read_only=True)
    dynamic_form_name = serializers.CharField(source="dynamic_form.name", read_only=True)

    class Meta:
        model = Employee
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "dynamic_form_id",
            "dynamic_form_name",
            "form_data",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "dynamic_form_id",
            "dynamic_form_name",
            "form_data",
            "created_at",
            "updated_at",
        ]


class EmployeeCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)
    form_id = serializers.IntegerField()
    answers = serializers.DictField()

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)
        return value

    def validate(self, attrs):
        email = (attrs.get("email") or "").strip()
        if email and User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "This email is already in use."})
        return attrs

    def create(self, validated_data):
        form_id = validated_data.pop("form_id")
        answers = validated_data.pop("answers")
        dynamic_form = DynamicForm.objects.filter(pk=form_id).first()
        if not dynamic_form:
            raise serializers.ValidationError({"form_id": "Invalid form id."})

        cleaned, err = validate_and_clean_form_data(dynamic_form, answers)
        if err:
            raise serializers.ValidationError({"answers": err})

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=validated_data["username"],
                    email=(validated_data.get("email") or "").strip(),
                    password=validated_data["password"],
                    first_name=validated_data.get("first_name") or "",
                    last_name=validated_data.get("last_name") or "",
                )
                employee = Employee.objects.create(
                    user=user,
                    dynamic_form=dynamic_form,
                    form_data=cleaned,
                )
        except IntegrityError as exc:
            raise serializers.ValidationError(
                "Could not create user (duplicate username or email)."
            ) from exc

        return employee


class EmployeeUpdateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, required=False)
    email = serializers.EmailField(required=False, allow_blank=True)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    form_id = serializers.IntegerField(required=False)
    answers = serializers.DictField(required=False, allow_empty=True)

    def validate_username(self, value):
        instance = self.context.get("employee")
        qs = User.objects.filter(username=value)
        if instance:
            qs = qs.exclude(pk=instance.user_id)
        if qs.exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_email(self, value):
        email = (value or "").strip()
        instance = self.context.get("employee")
        if not email:
            return ""
        qs = User.objects.filter(email=email)
        if instance:
            qs = qs.exclude(pk=instance.user_id)
        if qs.exists():
            raise serializers.ValidationError("This email is already in use.")
        return email

    def validate_password(self, value):
        if not value:
            return value
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)
        return value

    def update(self, instance: Employee, validated_data):
        form_id = validated_data.pop("form_id", None)
        answers = validated_data.pop("answers", None)
        password = validated_data.pop("password", None)

        dynamic_form = instance.dynamic_form
        if form_id is not None:
            new_form = DynamicForm.objects.filter(pk=form_id).first()
            if not new_form:
                raise serializers.ValidationError({"form_id": "Invalid form id."})
            dynamic_form = new_form

        if answers is not None:
            cleaned, err = validate_and_clean_form_data(dynamic_form, answers)
            if err:
                raise serializers.ValidationError({"answers": err})
            instance.form_data = cleaned
            instance.dynamic_form = dynamic_form
        elif form_id is not None and form_id != instance.dynamic_form_id:
            raise serializers.ValidationError(
                {"answers": "Provide answers when changing form_id."}
            )

        user = instance.user
        if "username" in validated_data:
            user.username = validated_data["username"]
        if "email" in validated_data:
            user.email = validated_data["email"] or ""
        if "first_name" in validated_data:
            user.first_name = validated_data["first_name"] or ""
        if "last_name" in validated_data:
            user.last_name = validated_data["last_name"] or ""
        if password:
            user.set_password(password)

        try:
            with transaction.atomic():
                user.save()
                instance.save()
        except IntegrityError as exc:
            raise serializers.ValidationError(
                "Could not save (duplicate username or email)."
            ) from exc

        return instance
