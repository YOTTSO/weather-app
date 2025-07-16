from django.urls import path
from .views import weather_view, history_view

urlpatterns = [
    path('', weather_view, name='weather_view'),
    path('history/', history_view, name='history_view'),
]