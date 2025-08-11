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


def get_time_grouping_key(history_record, period):
    """Returns a key for grouping history records by a given time period."""
    if period == "hour":
        return (
            history_record.group_member_id,
            history_record.timestamp.strftime("%Y-%m-%d %H"),
        )
    elif period == "day":
        return (history_record.group_member_id, history_record.timestamp.date())
    elif period == "week":
        return (
            history_record.group_member_id,
            history_record.timestamp.strftime("%Y-%U"),
        )
    return (
        history_record.group_member_id,
        history_record.timestamp,
    )  # Default for 'all'


def skill_history_data_api(request, skill_name):
    """
    API endpoint to fetch skill history data for multiple players,
    downsampling to the last data point per hour, day, or week.
    """
    player_names_str = request.GET.get("players", "")
    if not player_names_str:
        return JsonResponse({"error": "No players selected"}, status=400)

    player_names = player_names_str.split(",")
    period = request.GET.get("period", "all")

    history_query = PlayerHistory.objects.filter(
        group_member__player_name__in=player_names
    ).order_by("timestamp")

    downsampled_records = []

    if period == "all":
        downsampled_records = list(history_query)
    else:
        # UPDATED: Use the new helper function
        for key, group in groupby(
            history_query, key=lambda h: get_time_grouping_key(h, period)
        ):
            downsampled_records.append(list(group)[-1])

    if not downsampled_records:
        return JsonResponse({"timestamps": [], "datasets": []})

    # The rest of the function remains the same...
    timestamps = sorted(list(set(h.timestamp for h in downsampled_records)))
    formatted_timestamps = [ts.strftime("%Y-%m-%d %H:%M") for ts in timestamps]

    datasets = []
    for player_name in player_names:
        player_history = [
            h for h in downsampled_records if h.group_member.player_name == player_name
        ]

        value_map = {}
        if skill_name == "overall":
            for h in player_history:
                value_map[h.timestamp] = h.data.get("data", {}).get("Overall", 0)
        else:
            for h in player_history:
                value_map[h.timestamp] = h.data.get("data", {}).get(
                    skill_name.capitalize(), 0
                )

        skill_values = [value_map.get(ts) for ts in timestamps]

        datasets.append(
            {
                "label": player_name,
                "data": skill_values,
            }
        )

    response_data = {"timestamps": formatted_timestamps, "datasets": datasets}
    return JsonResponse(response_data)
