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


def player_history_api_view(request, player_name):
    """
    Retrieves a player's historical stats and prepares them for a graph.
    This view returns a JSON response, which is ideal for a JavaScript
    charting library on the front end.
    """
    # Get the GroupMember object for the given player name.
    # The get_object_or_404 function will raise an Http404 if the player is not found.
    group_member = get_object_or_404(GroupMember, player_name=player_name)

    # Get all historical records for this player, ordered by timestamp.
    history_records = PlayerHistory.objects.filter(group_member=group_member).order_by(
        "timestamp"
    )

    # Check if there's any historical data.
    if not history_records:
        return JsonResponse(
            {"error": "No historical data found for this player."}, status=404
        )

    # Prepare data for charting. We'll store timestamps and the values for a specific stat.
    timestamps = []
    overall_xp = []
    vorkath_kc = []

    # Iterate through the records to extract the data.
    for record in history_records:
        timestamps.append(record.timestamp.strftime("%Y-%m-%d %H:%M"))

        # Extract the Overall XP value.
        # The data is stored as a JSONField, so we can access it like a dictionary.
        overall_xp_value = record.data.get("data", {}).get("Overall", 0)
        overall_xp.append(overall_xp_value)

        # Extract the Vorkath kill count value.
        vorkath_kc_value = record.data.get("data", {}).get("Vorkath_killcount", 0)
        vorkath_kc.append(vorkath_kc_value)

    # Return the data as a JSON response.
    # This is a good way to separate the backend logic from the front-end rendering.
    return JsonResponse(
        {
            "player_name": player_name,
            "timestamps": timestamps,
            "overall_xp": overall_xp,
            "vorkath_kc": vorkath_kc,
        }
    )


def player_history_page(request, player_name):
    """
    Renders the HTML page for a player's historical stats.
    The JavaScript on the page will fetch the data separately.
    """
    # Check if the player exists before rendering the page.
    # This will return a 404 if the player_name is invalid.
    get_object_or_404(GroupMember, player_name=player_name)
    # The path has been updated to include the 'stats_app/' subdirectory.
    return render(request, "stats_app/player_history.html")
