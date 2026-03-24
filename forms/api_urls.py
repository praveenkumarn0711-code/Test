from django.urls import path

from .api_views import DynamicFormCreateAPIView

urlpatterns = [
    path("create/", DynamicFormCreateAPIView.as_view(), name="dynamic-form-api-create"),
]
