# stats_app/views.py

from .api_handler import parse_skills, parse_bosses, load_config, PlayerStats
from django.shortcuts import render
from django.http import JsonResponse
from .models import GroupMember, PlayerHistory, PlayerStatsCache


# stats_app/views.py


def player_stats_view(request):
    """
    View to display player stats directly from the cache.
    """
    all_cached_stats = PlayerStatsCache.objects.all().order_by(
        "group_member__player_name"
    )
    all_players_data = []
    config = load_config()  # Load the config once

    for cache_entry in all_cached_stats:
        # Get the raw JSON data from the cache entry
        api_response = cache_entry.data
        if not api_response or "data" not in api_response:
            continue  # Skip if this cache entry is malformed

        player_info = api_response.get("data", {}).get("info", {})
        player_data = api_response.get("data", {})

        # Skip if essential dictionaries are missing
        if not player_info or not player_data:
            continue

        # Use the same parsing logic from your api_handler
        parsed_skills = parse_skills(player_data, config)
        parsed_bosses = parse_bosses(player_data, config)

        # Re-create the PlayerStats object to pass to the template
        player_stats_object = PlayerStats(
            player_name=player_info.get("Username", "Unknown"),
            timestamp=player_info.get("Last checked", "N/A"),
            skills=parsed_skills,
            bosses=parsed_bosses,
        )
        all_players_data.append(player_stats_object)

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
            skill_values = [h.data.get("data", {}).get("Overall", 0) for h in history]
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
