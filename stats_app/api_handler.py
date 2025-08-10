# stats_app/api_handler.py

import requests
import json
from datetime import timedelta
from django.utils import timezone
from .models import GroupMember, PlayerStatsCache, APICallLog, PlayerHistory
from requests.exceptions import RequestException
import os
from urllib.parse import quote
import time


class Skill:
    def __init__(self, rank: int, level: int, xp: int):
        self.rank = rank
        self.level = level
        self.xp = xp


class Boss:
    def __init__(self, killcount: int):
        self.killcount = killcount


class PlayerStats:
    def __init__(self, player_name: str, timestamp: str, skills: dict, bosses: dict):
        self.player_name = player_name
        self.timestamp = timestamp
        self.skills = skills
        self.bosses = bosses


def load_config():
    """Loads configuration from config.json."""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "config.json")
        with open(config_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: config.json not found. Please create one.")
        return {}


def update_player_on_temple(player_name, max_requests_per_minute):
    """
    Triggers a stat update for a player on the TempleOSRS website
    by making a GET request to the add_datapoint.php endpoint.
    This function is rate-limited using a database to prevent excessive requests.
    Returns True on success, False otherwise.
    """
    one_minute_ago = timezone.now() - timedelta(seconds=60)
    recent_requests = APICallLog.objects.filter(timestamp__gte=one_minute_ago)

    if recent_requests.count() >= max_requests_per_minute:
        print(f"Rate limit reached. Skipping update for {player_name}.")
        return False

    try:
        encoded_player_name = quote(player_name)
        url = (
            f"https://templeosrs.com/php/add_datapoint.php?player={encoded_player_name}"
        )

        response = requests.get(url, timeout=10)
        response.raise_for_status()
        print(f"Successfully triggered update for {player_name} on TempleOSRS.")

        APICallLog.objects.create()
        return True

    except RequestException as e:
        print(f"Failed to trigger update for {player_name}: {e}")
        return False


def fetch_player_stats_from_api(player_name):
    """
    Fetch player stats from the TempleOSRS API.
    Raises RequestException on failure.
    Returns the parsed JSON response.
    """
    url = f"https://templeosrs.com/api/player_stats.php?player={player_name}&bosses=1"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def get_player_stats(player_name):
    """
    Fetches player stats based on the requested logic.
    """
    try:
        member = GroupMember.objects.get(player_name=player_name)
    except GroupMember.DoesNotExist:
        return None

    config = load_config()
    max_requests = config.get("api_rate_limit", {}).get("max_requests_per_minute", 5)
    api_response = None

    # Attempt to trigger an update on TempleOSRS first.
    update_successful = update_player_on_temple(player_name, max_requests)

    if update_successful:
        # If the update trigger was successful, we fetch the new data
        time.sleep(2)
        print(f"Update trigger successful. Now fetching new data for {player_name}...")
        try:
            api_response = fetch_player_stats_from_api(player_name)

            PlayerHistory.objects.create(group_member=member, data=api_response)

            # Now check if a cache entry exists and update it, or create a new one.
            cache, created = PlayerStatsCache.objects.get_or_create(
                group_member=member, defaults={"data": api_response}
            )
            if not created:
                cache.data = api_response
                cache.last_updated = timezone.now()
                cache.save()
        except RequestException as e:
            print(
                f"Failed to fetch new data after successful update trigger. Cannot update stats: {e}"
            )
            api_response = None

    # If the update trigger was not successful fall back to checking the cache.
    if api_response is None:
        try:
            cache = PlayerStatsCache.objects.get(group_member=member)
            print(f"Using cached data for {player_name}.")
            api_response = cache.data
        except PlayerStatsCache.DoesNotExist:
            print(
                f"No cached data and update failed for {player_name}. Cannot retrieve stats."
            )
            return None

    # This handles the case where there's no cache and the update failed.
    if api_response is None:
        return None

    player_info = api_response["data"]["info"]
    player_data = api_response["data"]

    parsed_skills = parse_skills(player_data, config)
    parsed_bosses = parse_bosses(player_data, config)

    player_stats_object = PlayerStats(
        player_name=player_info["Username"],
        timestamp=player_info["Last checked"],
        skills=parsed_skills,
        bosses=parsed_bosses,
    )

    return player_stats_object


def parse_skills(player_data, config):
    """Helper function to parse skill data."""
    config_skills = config.get("skills", [])
    parsed_skills = {}
    for skill_name in config_skills:
        skill_key = skill_name.lower()
        rank = player_data.get(f"{skill_name}_rank", 0)
        level = player_data.get(f"{skill_name}_level", 0)
        xp = player_data.get(skill_name, 0)
        parsed_skills[skill_key] = Skill(rank=rank, level=level, xp=xp)

    overall_skill_data = player_data.get("Overall", 0)
    overall_rank = player_data.get("Overall_rank", 0)
    overall_level = player_data.get("Overall_level", 0)
    parsed_skills["overall"] = Skill(
        rank=overall_rank, level=overall_level, xp=overall_skill_data
    )

    return parsed_skills


def parse_bosses(player_data, config):
    """Helper function to parse and sort boss data."""
    config_bosses = config.get("bosses", [])
    parsed_bosses = {}
    for boss_name in config_bosses:
        boss_key = boss_name.lower()
        killcount = player_data.get(f"{boss_name}", 0)
        parsed_bosses[boss_key] = Boss(killcount=killcount)

    sorted_bosses_list = sorted(
        parsed_bosses.items(), key=lambda item: item[1].killcount, reverse=True
    )
    return sorted_bosses_list
