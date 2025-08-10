# stats_app/views.py

from django.shortcuts import render
from .api_handler import get_player_stats
from .models import GroupMember  # Import your new model


def player_stats_view(request):
    # Retrieve all GroupMember objects from the database
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
