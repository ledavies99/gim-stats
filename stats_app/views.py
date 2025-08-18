# stats_app/views.py

from django.shortcuts import render
from django.http import JsonResponse
from .models import GroupMember, PlayerHistory
from .api_handler import get_player_stats_from_cache, load_config

from datetime import datetime


def get_xp_gained_today(player, skill_names):
    """
    Returns a tuple: (total_xp_gained_today, skill_xp_gained_today_dict)
    """
    today = datetime.now().date()
    histories = PlayerHistory.objects.filter(group_member=player).order_by("timestamp")
    today_histories = histories.filter(timestamp__date=today)
    skill_gains = {}
    if today_histories.exists():
        first = today_histories.first().data["data"]
        last = today_histories.last().data["data"]
        for skill in skill_names:
            first_xp = first.get(skill.capitalize(), 0)
            last_xp = last.get(skill.capitalize(), 0)
            skill_gains[skill] = last_xp - first_xp
        total = skill_gains.get("Overall", 0)
    else:
        for skill in skill_names:
            skill_gains[skill] = 0
        total = 0
    return total, skill_gains


def player_stats_view(request):
    """
    View to display player stats directly from the cache.
    """
    all_players = GroupMember.objects.all().order_by("player_name")
    all_players_data = []

    skill_names = load_config().get("skills", [])
    for player in all_players:
        stats = get_player_stats_from_cache(player.player_name)
        if stats:
            total_xp, skill_xp_gained_today = get_xp_gained_today(player, skill_names)
            stats.xp_gained_today = total_xp
            stats.skill_xp_gained_today = skill_xp_gained_today
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
    API endpoint to fetch all skill history data for multiple players,
    keeping only the first and last point of each run of identical y-values.
    """
    player_names_str = request.GET.get("players", "")
    ymode = request.GET.get("ymode", "xp")
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

        chart_data = []
        value_key = skill_name.capitalize()
        level_key = f"{value_key}_level"  # e.g. "Attack_level"
        prev_y = None
        run_start = None

        history_list = list(history_query)
        for i, record in enumerate(history_list):
            if ymode == "level":
                y_val = int(record.data.get("data", {}).get(level_key, 1) or 1)
            else:
                y_val = int(record.data.get("data", {}).get(value_key, 0) or 0)
            if prev_y is None or y_val != prev_y:
                if run_start is not None and i > 0:
                    last_record = history_list[i - 1]
                    if ymode == "level":
                        last_y = int(
                            last_record.data.get("data", {}).get(level_key, 1) or 1
                        )
                    else:
                        last_y = int(
                            last_record.data.get("data", {}).get(value_key, 0) or 0
                        )
                    if last_record.timestamp != run_start.timestamp:
                        chart_data.append(
                            {
                                "x": last_record.timestamp.strftime(
                                    "%Y-%m-%dT%H:%M:%S"
                                ),
                                "y": last_y,
                            }
                        )
                chart_data.append(
                    {
                        "x": record.timestamp.strftime("%Y-%m-%dT%H:%M:%S"),
                        "y": y_val,
                    }
                )
                run_start = record
            prev_y = y_val

        if history_list:
            last_record = history_list[-1]
            if ymode == "level":
                last_y = int(last_record.data.get("data", {}).get(level_key, 1) or 1)
            else:
                last_y = int(last_record.data.get("data", {}).get(value_key, 0) or 0)
            if not chart_data or chart_data[-1]["x"] != last_record.timestamp.strftime(
                "%Y-%m-%dT%H:%M:%S"
            ):
                chart_data.append(
                    {
                        "x": last_record.timestamp.strftime("%Y-%m-%dT%H:%M:%S"),
                        "y": last_y,
                    }
                )

        datasets.append(
            {
                "label": player_name,
                "data": chart_data,
            }
        )

    return JsonResponse({"datasets": datasets})
