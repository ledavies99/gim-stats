# stats_app/api_handler.py

import requests
import json
from datetime import timedelta
from django.utils import timezone
from .models import GroupMember, PlayerStatsCache
from django.core.serializers.json import DjangoJSONEncoder


class Skill:
    def __init__(self, rank: int, level: int, xp: int):
        self.rank = rank
        self.level = level
        self.xp = xp

class Boss:
    def __init__(self, rank: int, killcount: int):
        self.rank = rank
        self.killcount = killcount

class PlayerStats:
    def __init__(self, player_name: str, timestamp: str, skills: dict, bosses: dict):
        self.player_name = player_name
        self.timestamp = timestamp
        self.skills = skills
        self.bosses = bosses


def get_player_stats(player_name):
    """
    Fetches and parses player stats, using caching to avoid repeated API calls.
    """
    try:
        member = GroupMember.objects.get(player_name=player_name)
    except GroupMember.DoesNotExist:
        print(f"Error: Group member '{player_name}' not found in the database.")
        return None

    # Check for cached data
    try:
        cache = PlayerStatsCache.objects.get(group_member=member)
        # Define cache expiration time (e.g., 1 hour)
        if timezone.now() - cache.timestamp < timedelta(hours=1):
            # Data is recent, use the cached data
            print(f"Using cached data for {player_name}")
            api_response = cache.data
        else:
            # Data is stale, fetch a new response
            print(f"Cached data for {player_name} is stale. Fetching new data...")
            url = f"https://templeosrs.com/api/player_stats.php?player={player_name}"
            response = requests.get(url)
            response.raise_for_status()
            api_response = response.json()

            # Update the cache
            cache.data = api_response
            cache.save()
    except PlayerStatsCache.DoesNotExist:
        # No cached data exists, fetch a new response
        print(f"No cached data for {player_name}. Fetching new data...")
        url = f"https://templeosrs.com/api/player_stats.php?player={player_name}"
        response = requests.get(url)
        response.raise_for_status()
        api_response = response.json()

        # Create a new cache entry
        PlayerStatsCache.objects.create(group_member=member, data=api_response)

    player_info = api_response['data']['info']
    player_data = api_response['data']

    parsed_skills = {}
    skill_names = [
        'Attack', 'Hitpoints', 'Mining', 
        'Strength', 'Agility', 'Smithing', 
        'Defence','Herblore', 'Fishing', 
        'Ranged', 'Thieving', 'Cooking', 
        'Prayer', 'Crafting','Firemaking', 
        'Magic', 'Fletching', 'Woodcutting', 
        'Runecraft', 'Slayer', 'Farming',
        'Construction', 'Hunter', 'Overall'
    ]

    for skill_name in skill_names:
        skill_key = skill_name.lower()
        rank = player_data.get(f'{skill_name}_rank', 0)
        level = player_data.get(f'{skill_name}_level', 0)
        xp = player_data.get(skill_name, 0)
        parsed_skills[skill_key] = Skill(rank=rank, level=level, xp=xp)

    parsed_bosses = {}

    return PlayerStats(
        player_name=player_info['Username'],
        timestamp=player_info['Last checked'],
        skills=parsed_skills,
        bosses=parsed_bosses,
    )
