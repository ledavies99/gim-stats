# stats_app/views.py

from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.views.decorators.http import require_GET
from .models import GroupMember, PlayerHistory
from .api_handler import get_player_stats_from_cache, load_config
from .utils import get_keys
from datetime import datetime, timedelta


# Serve React index.html for the main frontend
class ReactAppView(TemplateView):
    template_name = "index.html"

    def get(self, request, *args, **kwargs):
        return self.render_to_response({})


@require_GET
def player_stats_api(request):
    from .models import PlayerStatsCache

    skill_names = load_config().get("skills", [])
    all_players = list(GroupMember.objects.all().order_by("player_name"))
    caches = PlayerStatsCache.objects.select_related("group_member").in_bulk(
        [p.id for p in all_players], field_name="group_member_id"
    )
    all_players_data = [
        annotate_player_stats(player, skill_names, cache=caches.get(player.id))
        for player in all_players
    ]
    all_players_data = [p for p in all_players_data if p]
    all_players_data.sort(key=lambda p: p.xp_gained_week, reverse=True)
    for idx, player in enumerate(all_players_data):
        player.rank = idx + 1

    players_ordered = order_players_for_podium(all_players_data)

    data = []
    for p in players_ordered:
        # Convert skills and bosses to plain dicts
        skills = {
            k: v if isinstance(v, dict) else v.__dict__
            for k, v in getattr(p, "skills", {}).items()
        }
        bosses = {
            k: v if isinstance(v, dict) else v.__dict__
            for k, v in getattr(p, "bosses", {}).items()
        }

        # Optionally, filter out any non-serializable fields from v.__dict__ if needed

        data.append(
            {
                "player_name": p.player_name,
                "rank": p.rank,
                "timestamp": getattr(p, "timestamp", None),
                "skills": skills,
                "bosses": bosses,
                "xp_gained_today": getattr(p, "xp_gained_today", 0),
                "top_skill_today": getattr(p, "top_skill_today", None),
                "skill_xp_gained_today": getattr(p, "skill_xp_gained_today", []),
                "xp_gained_week": getattr(p, "xp_gained_week", 0),
                "top_skill_week": getattr(p, "top_skill_week", None),
                "skill_xp_gained_week": getattr(p, "skill_xp_gained_week", []),
            }
        )

    return JsonResponse({"players": data})


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
    DATA_KEY, _, OVERALL_KEY, _, _ = get_keys()
    if histories.exists():
        first = getattr(histories.first(), "data", {}).get(DATA_KEY, {})
        last = getattr(histories.last(), "data", {}).get(DATA_KEY, {})
        for skill in skill_names:
            try:
                first_xp = int(first.get(skill.capitalize(), 0) or 0)
                last_xp = int(last.get(skill.capitalize(), 0) or 0)
            except (ValueError, TypeError):
                first_xp = 0
                last_xp = 0
            skill_gains[skill] = last_xp - first_xp
        total = skill_gains.get(OVERALL_KEY, 0)
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


def annotate_player_stats(player, skill_names, cache=None):
    stats = get_player_stats_from_cache(player.player_name, cache=cache)
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
    View to display player stats directly from the cache, optimized to avoid N+1 queries.
    """
    from .models import PlayerStatsCache

    skill_names = load_config().get("skills", [])
    # Prefetch PlayerStatsCache for all players
    all_players = list(GroupMember.objects.all().order_by("player_name"))
    caches = PlayerStatsCache.objects.select_related("group_member").in_bulk(
        [p.id for p in all_players], field_name="group_member_id"
    )
    all_players_data = [
        annotate_player_stats(player, skill_names, cache=caches.get(player.id))
        for player in all_players
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


def extract_y_value(record, value_key, level_key, ymode):
    """
    Returns the correct y-value (XP or level) from a PlayerHistory record.
    """
    DATA_KEY, _, _, _, _ = get_keys()
    data = getattr(record, "data", {}).get(DATA_KEY, {})
    try:
        if ymode == "level":
            return int(data.get(level_key, 1) or 1)
        else:
            return int(data.get(value_key, 0) or 0)
    except (ValueError, TypeError):
        return 1 if ymode == "level" else 0


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
        try:
            history_query = PlayerHistory.objects.filter(
                group_member__player_name=player_name
            ).order_by("timestamp")
        except Exception:
            continue

        if not history_query.exists():
            continue

        chart_data = []
        value_key = skill_name.capitalize()
        level_key = f"{value_key}_level"
        prev_y = None
        run_start = None

        history_list = list(history_query)
        for i, record in enumerate(history_list):
            y_val = extract_y_value(record, value_key, level_key, ymode)
            # Only add a new point if the value changes (to reduce chart noise)
            if prev_y is None or y_val != prev_y:
                # If this is not the first run, add the last point of the previous run
                if run_start is not None and i > 0:
                    last_record = history_list[i - 1]
                    last_y = extract_y_value(last_record, value_key, level_key, ymode)
                    # Avoid duplicate timestamps
                    if last_record.timestamp != run_start.timestamp:
                        chart_data.append(
                            {
                                "x": last_record.timestamp.strftime(
                                    "%Y-%m-%dT%H:%M:%S"
                                ),
                                "y": last_y,
                            }
                        )
                # Add the new point where the value changes
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
            last_y = extract_y_value(last_record, value_key, level_key, ymode)
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
