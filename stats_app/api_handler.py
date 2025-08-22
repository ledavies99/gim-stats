# stats_app/api_handler.py


import requests
import json
import os
from datetime import timedelta
from urllib.parse import quote
from django.utils import timezone
from .models import GroupMember, PlayerStatsCache, APICallLog, PlayerHistory
from requests.exceptions import RequestException

from dataclasses import dataclass


def get_keys():
    config = load_config()
    keys = config.get("keys", {})
    return (
        keys.get("data", "data"),
        keys.get("info", "info"),
        keys.get("overall", "Overall"),
        keys.get("overall_rank", "Overall_rank"),
        keys.get("overall_level", "Overall_level"),
    )


@dataclass
class Skill:
    rank: int
    level: int
    xp: int


@dataclass
class Boss:
    killcount: int


@dataclass
class PlayerStats:
    player_name: str
    timestamp: str
    skills: dict
    bosses: dict


def refresh_player_cache(player_name):
    """
    Handles the "heavy lifting": triggers an API update, fetches fresh data,
    and saves it to the PlayerStatsCache.
    Returns True on success, False on failure.
    """
    try:
        member = GroupMember.objects.get(player_name=player_name)
    except GroupMember.DoesNotExist:
        return False

    config = load_config()
    DATA_KEY, INFO_KEY, OVERALL_KEY, OVERALL_RANK_KEY, OVERALL_LEVEL_KEY = get_keys()
    max_requests = config.get("api_rate_limit", {}).get("max_requests_per_minute", 5)

    if update_player_on_temple(player_name, max_requests):
        try:
            api_response = fetch_player_stats_from_api(player_name)

            skill_names = config.get("skills", [])

            try:
                last_history = (
                    PlayerHistory.objects.filter(group_member=member)
                    .only("data")
                    .latest("timestamp")
                )
                previous_data = last_history.data.get("data", {})
            except PlayerHistory.DoesNotExist:
                previous_data = {}

            api_data = api_response.get(DATA_KEY, {})
            for skill in skill_names:
                # XP carry-forward
                xp = carry_forward(api_data.get(skill), previous_data.get(skill, 0))
                api_data[skill] = xp

                # Level carry-forward
                level_key = f"{skill}_level"
                level = carry_forward(
                    api_data.get(level_key), previous_data.get(level_key, 0)
                )
                api_data[level_key] = level

            api_response[DATA_KEY] = api_data

            cache, created = PlayerStatsCache.objects.get_or_create(
                group_member=member, defaults={DATA_KEY: api_response}
            )
            if not created:
                cache.data = api_response
                cache.last_updated = timezone.now()
                cache.save()

            PlayerHistory.objects.create(
                group_member=member, timestamp=cache.last_updated, data=api_response
            )
            return True  # Success
        except RequestException:
            return False  # Failed to fetch new data
    return False  # Rate limit was likely hit


def get_player_stats_from_cache(player_name):
    """
    Handles the "fast" part: reads and parses data directly from the cache.
    """

    try:
        member = GroupMember.objects.get(player_name=player_name)
        cache = PlayerStatsCache.objects.get(group_member=member)
        api_response = cache.data
    except (GroupMember.DoesNotExist, PlayerStatsCache.DoesNotExist):
        return None

    DATA_KEY, INFO_KEY, OVERALL_KEY, OVERALL_RANK_KEY, OVERALL_LEVEL_KEY = get_keys()
    if not api_response or DATA_KEY not in api_response:
        return None

    config = load_config()
    player_info = api_response.get(DATA_KEY, {}).get(INFO_KEY, {})
    player_data = api_response.get(DATA_KEY, {})

    if not player_info or not player_data:
        return None

    parsed_skills = parse_skills(player_data, config)
    parsed_bosses = parse_bosses(player_data, config)

    return PlayerStats(
        player_name=member.player_name,
        timestamp=player_info.get("Last checked", "N/A"),
        skills=parsed_skills,
        bosses=parsed_bosses,
    )


def parse_skills(player_data, config):
    """Parse skills from player data using the provided config."""
    skill_names = config.get("skills", [])
    parsed_skills = {}
    for skill_name in skill_names:
        skill_key = skill_name.lower()
        rank = player_data.get(f"{skill_name}_rank", 0)
        level = player_data.get(f"{skill_name}_level", 0)
        xp = player_data.get(skill_name, 0)
        parsed_skills[skill_key] = Skill(rank=rank, level=level, xp=xp)

    _, _, OVERALL_KEY, OVERALL_RANK_KEY, OVERALL_LEVEL_KEY = get_keys()
    overall_skill_data = player_data.get(OVERALL_KEY, 0)
    overall_rank = player_data.get(OVERALL_RANK_KEY, 0)
    overall_level = player_data.get(OVERALL_LEVEL_KEY, 0)
    parsed_skills["overall"] = Skill(
        rank=overall_rank, level=overall_level, xp=overall_skill_data
    )

    return parsed_skills


def parse_bosses(player_data, config):
    """Parse bosses from player data using the provided config."""
    boss_names = config.get("bosses", [])
    parsed_bosses = {}
    for boss_name in boss_names:
        boss_key = boss_name.lower()
        killcount = player_data.get(f"{boss_name}", 0)
        parsed_bosses[boss_key] = Boss(killcount=killcount)

    sorted_bosses_list = dict(
        sorted(parsed_bosses.items(), key=lambda item: item[1].killcount, reverse=True)
    )
    return sorted_bosses_list


def update_player_on_temple(player_name, max_requests_per_minute):
    """Updates the player's stats on the TempleOSRS API.
    Returns True if the update was successful, False if it hit the rate limit.
    """
    # Check if the rate limit has been hit
    one_minute_ago = timezone.now() - timedelta(seconds=60)
    recent_requests = APICallLog.objects.filter(timestamp__gte=one_minute_ago)

    if recent_requests.count() >= max_requests_per_minute:
        return False

    try:
        encoded_player_name = quote(player_name)
        url = (
            f"https://templeosrs.com/php/add_datapoint.php?player={encoded_player_name}"
        )
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        APICallLog.objects.create()
        return True
    except RequestException:
        return False


def fetch_player_stats_from_api(player_name):
    """Fetches player stats from the TempleOSRS API."""
    encoded_player_name = quote(player_name)
    url = f"https://templeosrs.com/api/player_stats.php?player={encoded_player_name}&bosses=1"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def carry_forward(new_value, prev_value):
    """Carry forward the value if it's None or less than the previous value."""
    if new_value is None:
        return prev_value
    if new_value < prev_value:
        return prev_value
    return new_value


def load_config():
    """Loads the configuration from a JSON file."""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "config.json")
        with open(config_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
