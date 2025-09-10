# stats_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path(
        "api/history_data/<str:skill_name>/",
        views.skill_history_data_api,
        name="skill_history_data_api",
    ),
    path("api/player_stats/", views.player_stats_api, name="player_stats_api"),
]
