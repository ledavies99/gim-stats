# stats_app/views.py

from django.shortcuts import render
from .api_handler import get_player_stats

def player_stats_view(request):
    # A list of your group's player names
    player_names = ["Bogsloppit", "BonskFEey", "Shiba Jab"]
    
    all_players_data = []

    for name in player_names:
        stats = get_player_stats(name)
        if stats:
            all_players_data.append(stats)

    context = {
        'players': all_players_data
    }

    return render(request, 'stats_app/player_stats.html', context)