# stats_app/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.player_stats_view, name='player_stats'),
]