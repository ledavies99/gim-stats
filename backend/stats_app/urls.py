# stats_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Main page with a list of all players and their current stats
    path("", views.player_stats_view, name="player_stats_view"),
    # URL for the new skill history page (e.g., /history/attack/)
    path("history/<str:skill_name>/", views.skill_history_view, name="skill_history"),
    # URL for the new data API endpoint
    path(
        "api/history_data/<str:skill_name>/",
        views.skill_history_data_api,
        name="skill_history_data_api",
    ),
    path("api/player_stats/", views.player_stats_api, name="player_stats_api"),
]
