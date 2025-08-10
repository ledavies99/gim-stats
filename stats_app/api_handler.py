# stats_app/api_handler.py

import requests
import json
from pathlib import Path
from datetime import timedelta
from django.utils import timezone
from .models import GroupMember, PlayerStatsCache
from requests.exceptions import RequestException  # Add this import


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
    base_dir = Path(__file__).resolve().parent
    config_path = base_dir / "config.json"

    if not config_path.exists():
        print(f"Error: The configuration file was not found at {config_path}")
        return {"skills": [], "bosses": []}

    with open(config_path, "r") as f:
        return json.load(f)


def fetch_player_stats_from_api(player_name):
    """
    Fetch player stats from the TempleOSRS API.
    Raises RequestException on failure.
    Returns the parsed JSON response.
    """
    url = f"https://templeosrs.com/api/player_stats.php?player={player_name}&bosses=1"
    response = requests.get(url)
    response.raise_for_status()  # Raises exception for bad status codes
    return response.json()


def get_player_stats(player_name):
    """
    Fetches and parses player stats, using caching to avoid repeated API calls.
    Gracefully falls back to cached data if the API call fails.
    """
    api_response = None
    member = None

    try:
        member = GroupMember.objects.get(player_name=player_name)
    except GroupMember.DoesNotExist:
        print(f"Error: Group member '{player_name}' not found in the database.")
        return None

    try:
        cache = PlayerStatsCache.objects.get(group_member=member)
        # Try to fetch new data if cache is stale (or on error)
        if timezone.now() - cache.timestamp >= timedelta(hours=1):
            print(
                f"Cached data for {player_name} is stale. Attempting to fetch new data..."
            )
            try:
                api_response = fetch_player_stats_from_api(player_name)
                print(f"Successfully fetched new data for {player_name}.")

                # Update the cache with the new data
                cache.data = api_response
                cache.save()
            except RequestException as e:
                # If fetching new data fails, fall back to the existing cache
                print(f"API request failed for {player_name}: {e}. Using cached data.")
                api_response = cache.data
        else:
            # Data is recent, use the cached data
            print(f"Using cached data for {player_name}")
            api_response = cache.data

    except PlayerStatsCache.DoesNotExist:
        # No cached data exists, so we must fetch a new response.
        print(f"No cached data for {player_name}. Attempting to fetch new data...")
        try:
            api_response = fetch_player_stats_from_api(player_name)
            print(f"Successfully fetched new data for {player_name}.")

            # Create a new cache entry
            PlayerStatsCache.objects.create(group_member=member, data=api_response)
        except RequestException as e:
            print(f"API request failed for {player_name}: {e}. Cannot display stats.")
            return None

    if not api_response:
        return None

    # Parsing the API response
    player_info = api_response["data"]["info"]
    player_data = api_response["data"]

    config = load_config()
    skill_names = config.get("skills", [])
    boss_names = config.get("bosses", [])

    parsed_skills = {}
    for skill_name in skill_names:
        skill_key = skill_name.lower()
        rank = player_data.get(f"{skill_name}_rank", 0)
        level = player_data.get(f"{skill_name}_level", 0)
        xp = player_data.get(skill_name, 0)
        parsed_skills[skill_key] = Skill(rank=rank, level=level, xp=xp)

    parsed_bosses = {}
    for boss_name in boss_names:
        boss_key = boss_name.lower()
        killcount = player_data.get(f"{boss_name}", 0)
        parsed_bosses[boss_key] = Boss(killcount=killcount)

    sorted_bosses_list = dict(
        sorted(parsed_bosses.items(), key=lambda item: item[1].killcount, reverse=True)
    )

    return PlayerStats(
        player_name=player_info["Username"],
        timestamp=player_info["Last checked"],
        skills=parsed_skills,
        bosses=sorted_bosses_list,
    )
