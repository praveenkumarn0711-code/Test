from django.urls import path
from .views import form_create_view


urlpatterns = [
    path('get-form/', form_create_view, name='get-form'),

]