# stats_app/views.py

from django.shortcuts import render
from django.http import JsonResponse
from .models import GroupMember, PlayerHistory
from .api_handler import get_player_stats_from_cache
from itertools import groupby


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
    API endpoint to fetch skill history data for multiple players,
    downsampling to the LAST data point per hour, day, or week.
    """
    player_names_str = request.GET.get("players", "")
    if not player_names_str:
        return JsonResponse({"error": "No players selected"}, status=400)

    player_names = player_names_str.split(",")
    period = request.GET.get("period", "all")

    datasets = []

    for player_name in player_names:
        # Base query for each player
        history_query = PlayerHistory.objects.filter(
            group_member__player_name=player_name
        ).order_by("timestamp")

        downsampled_records = []
        if period == "all":
            downsampled_records = list(history_query)
        else:

            def key_func_hour(h):
                return h.timestamp.strftime("%Y-%m-%d %H")

            def key_func_day(h):
                return h.timestamp.date()

            def key_func_week(h):
                return h.timestamp.strftime("%Y-%U")

            if period == "hour":
                key_func = key_func_hour
            elif period == "day":
                key_func = key_func_day
            elif period == "week":
                key_func = key_func_week

            # Group records by the key and take the LAST record from each group
            for key, group in groupby(history_query, key=key_func):
                downsampled_records.append(list(group)[-1])

        if not downsampled_records:
            continue

        # Prepare data points as {x, y} objects for Chart.js
        chart_data = []
        value_key = skill_name.capitalize()

        for record in downsampled_records:
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
