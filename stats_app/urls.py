# stats_app/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path("", views.player_stats_view, name="player_stats"),
    path(
        "history/<str:player_name>/", views.player_history_page, name="player_history"
    ),
    path(
        "history/data/<str:player_name>/",
        views.player_history_api_view,
        name="player_history_api",
    ),
]
