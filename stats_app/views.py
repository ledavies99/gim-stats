# stats_app/views.py

from .api_handler import get_player_stats
from django.shortcuts import render
from django.http import JsonResponse
from .models import GroupMember, PlayerHistory


def player_stats_view(request):
    """View to display player stats."""
    group_members = GroupMember.objects.all()

    # Extract the player names from the objects
    player_names = [member.player_name for member in group_members]

    all_players_data = []

    for name in player_names:
        stats = get_player_stats(name)
        if stats:
            all_players_data.append(stats)

    context = {"players": all_players_data}

    return render(request, "stats_app/player_stats.html", context)


def skill_history_view(request, skill_name):
    """View to display the skill history page."""
    all_players = GroupMember.objects.values("player_name").distinct()

    # Get the selected player's name from the URL query parameter
    selected_player_name = request.GET.get("player", None)

    context = {
        "skill_name": skill_name,
        "all_players": all_players,
        "selected_player_name": selected_player_name,  # Add to context
    }
    return render(request, "stats_app/skill_history.html", context)


def skill_history_data_api(request, skill_name):
    """API endpoint to fetch skill history data for multiple players."""
    player_names_str = request.GET.get("players", "")
    if not player_names_str:
        return JsonResponse({"error": "No players selected"}, status=400)

    player_names = player_names_str.split(",")

    first_player_history = PlayerHistory.objects.filter(
        group_member__player_name=player_names[0]
    ).order_by("timestamp")
    timestamps = [h.timestamp.strftime("%Y-%m-%d %H:%M") for h in first_player_history]

    datasets = []
    for player_name in player_names:
        history = PlayerHistory.objects.filter(
            group_member__player_name=player_name
        ).order_by("timestamp")

        if skill_name == "overall":
            skill_values = [
                h.data.get("data", {}).get("Overall_level", 0) for h in history
            ]
        else:
            skill_values = [
                h.data.get("data", {}).get(skill_name.capitalize(), 0) for h in history
            ]

        datasets.append(
            {
                "label": player_name,
                "data": skill_values,
            }
        )

    response_data = {"timestamps": timestamps, "datasets": datasets}
    return JsonResponse(response_data)
