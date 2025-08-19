# stats_app/views.py

from django.shortcuts import render
from django.http import JsonResponse
from .models import GroupMember, PlayerHistory
from .api_handler import get_player_stats_from_cache, load_config
from datetime import datetime, timedelta


def get_xp_gained_period(player, skill_names, days=1):
    """
    Returns a tuple: (total_xp_gained, sorted_skill_xp_gained)
    for the last `days` days (1 = today, 7 = last 7 days).
    """
    today = datetime.now().date()
    start_date = today - timedelta(days=days - 1)
    histories = PlayerHistory.objects.filter(
        group_member=player, timestamp__date__gte=start_date, timestamp__date__lte=today
    ).order_by("timestamp")
    skill_gains = {}
    if histories.exists():
        first = histories.first().data["data"]
        last = histories.last().data["data"]
        for skill in skill_names:
            first_xp = first.get(skill.capitalize(), 0)
            last_xp = last.get(skill.capitalize(), 0)
            skill_gains[skill] = last_xp - first_xp
        total = skill_gains.get("Overall", 0)
    else:
        for skill in skill_names:
            skill_gains[skill] = 0
        total = 0

    sorted_skill_gains = sorted(
        (
            (skill, xp)
            for skill, xp in skill_gains.items()
            if skill.lower() != "overall" and xp != 0
        ),
        key=lambda item: item[1],
        reverse=True,
    )

    return total, sorted_skill_gains


def order_players_for_podium(players):
    """
    Returns a list of players ordered as:
    [leftmost, ..., silver, gold, bronze, ..., rightmost]
    with gold in the center, silver to the left, bronze to the right,
    and the rest alternating left/right outward.
    """
    gold = next((p for p in players if p.rank == 1), None)
    silver = next((p for p in players if p.rank == 2), None)
    bronze = next((p for p in players if p.rank == 3), None)
    others = [p for p in players if p.rank > 3]

    ordered = [silver, gold, bronze]

    left = []
    right = []
    for i, p in enumerate(others):
        if i % 2 == 0:
            left.insert(0, p)
        else:
            right.append(p)

    return [p for p in (left + ordered + right) if p is not None]


def annotate_player_stats(player, skill_names):
    stats = get_player_stats_from_cache(player.player_name)
    if not stats:
        return None
    # Daily
    total_xp, skill_xp_gained_today = get_xp_gained_period(player, skill_names, days=1)
    stats.top_skill_today = (
        skill_xp_gained_today[0][0] if skill_xp_gained_today else None
    )
    stats.xp_gained_today = total_xp
    stats.skill_xp_gained_today = skill_xp_gained_today
    # Weekly
    total_weekly_xp, skill_xp_gained_week = get_xp_gained_period(
        player, skill_names, days=7
    )
    stats.top_skill_week = skill_xp_gained_week[0][0] if skill_xp_gained_week else None
    stats.xp_gained_week = total_weekly_xp
    stats.skill_xp_gained_week = skill_xp_gained_week
    return stats


def player_stats_view(request):
    """
    View to display player stats directly from the cache.
    """
    all_players = GroupMember.objects.all().order_by("player_name")
    all_players_data = []

    skill_names = load_config().get("skills", [])
    all_players_data = [
        annotate_player_stats(player, skill_names) for player in all_players
    ]
    all_players_data = [p for p in all_players_data if p]

    # Sort by weekly XP gained descending
    all_players_data.sort(key=lambda p: p.xp_gained_week, reverse=True)
    for idx, player in enumerate(all_players_data):
        player.rank = idx + 1  # 1-based rank

    players_ordered = order_players_for_podium(all_players_data)
    context = {"players": players_ordered}

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
