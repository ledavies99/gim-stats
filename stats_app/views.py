# stats_app/views.py

from django.shortcuts import render
from django.http import JsonResponse
from .models import GroupMember, PlayerHistory
from .api_handler import get_player_stats_from_cache


def player_stats_view(request):
    """
    View to display player stats directly from the cache.
    """
    all_players = GroupMember.objects.all().order_by("player_name")
    all_players_data = []

    for player in all_players:
        stats = get_player_stats_from_cache(player.player_name)
        if stats:
            all_players_data.append(stats)

    context = {"players": all_players_data}
    return render(request, "stats_app/player_stats.html", context)


def skill_history_view(request, skill_name):
    """View to display the skill history page."""
    all_players = GroupMember.objects.values("player_name").distinct()
    selected_player_name = request.GET.get("player", None)

    context = {
        "skill_name": skill_name,
        "all_players": all_players,
        "selected_player_name": selected_player_name,
    }
    return render(request, "stats_app/skill_history.html", context)


def skill_history_data_api(request, skill_name):
    """
    API endpoint to fetch all skill history data for multiple players.
    """
    player_names_str = request.GET.get("players", "")
    if not player_names_str:
        return JsonResponse({"error": "No players selected"}, status=400)

    player_names = player_names_str.split(",")

    datasets = []

    for player_name in player_names:
        history_query = PlayerHistory.objects.filter(
            group_member__player_name=player_name
        ).order_by("timestamp")

        if not history_query.exists():
            continue

        # Prepare data points as {x, y} objects for Chart.js
        chart_data = []
        value_key = skill_name.capitalize()

        for record in history_query:
            chart_data.append(
                {
                    "x": record.timestamp.strftime("%Y-%m-%dT%H:%M:%S"),
                    "y": int(record.data.get("data", {}).get(value_key, 0) or 0),
                }
            )

        datasets.append(
            {
                "label": player_name,
                "data": chart_data,
            }
        )

    return JsonResponse({"datasets": datasets})
