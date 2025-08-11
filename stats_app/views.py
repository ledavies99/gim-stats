# stats_app/views.py

from .api_handler import get_player_stats
from django.shortcuts import render, get_object_or_404
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


def player_history_view(request, player_name, skill_name):
    """View to display a player's historical stats chart."""
    # This view just renders the HTML page. The JavaScript will handle the data fetching.
    context = {
        "player_name": player_name,
        "skill_name": skill_name,
    }
    return render(request, "stats_app/player_history.html", context)


def player_history_api_view(request, player_name, skill_name):
    """
    Retrieves a player's historical stats for a specific skill and prepares
    them for a graph. This view now returns the data for the skill
    passed in the URL.
    """
    # Get the GroupMember object for the given player name, using a case-insensitive lookup.
    group_member = get_object_or_404(GroupMember, player_name__iexact=player_name)

    # Get all the PlayerHistory records for this player, ordered by timestamp.
    history_records = PlayerHistory.objects.filter(group_member=group_member).order_by(
        "timestamp"
    )

    # Prepare data for charting.
    timestamps = []
    skill_values = []

    # Capitalize the skill name to match the JSON key, e.g., 'attack' -> 'Attack'
    capitalized_skill_name = skill_name.capitalize()

    # Define the key for the value we want to track (XP or level)
    value_key = f"{capitalized_skill_name}"

    # Special case for the overall skill
    if skill_name.lower() == "overall":
        value_key = "Overall_level"

    # Iterate through the records to extract the data.
    for record in history_records:
        timestamps.append(record.timestamp.strftime("%Y-%m-%d %H:%M"))

        # Access the value using the constructed key
        history_data = record.data.get("data", {})
        skill_value = history_data.get(value_key, 0)

        skill_values.append(skill_value)

    # Return the data as a JSON response.
    return JsonResponse(
        {
            "player_name": player_name,
            "timestamps": timestamps,
            "skill_values": skill_values,
        }
    )


def skill_history_view(request, skill_name):
    """View to display the skill history page."""
    all_players = GroupMember.objects.values("player_name").distinct()
    context = {
        "skill_name": skill_name,
        "all_players": all_players,
    }
    return render(request, "stats_app/skill_history.html", context)


# stats_app/views.py


def skill_history_data_api(request, skill_name):
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
