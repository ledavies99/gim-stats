# stats_app/api_handler.py

import requests
import json

class Skill:
    """Represents a single Old School RuneScape skill's data."""
    def __init__(self, rank: int, level: int, xp: int):
        self.rank = rank
        self.level = level
        self.xp = xp

class Boss:
    """Represents a single Old School RuneScape boss's data."""
    def __init__(self, rank: int, killcount: int):
        self.rank = rank
        self.killcount = killcount

class PlayerStats:
    """Represents all parsed stats for a single Old School RuneScape player."""
    def __init__(self, player_name: str, timestamp: str, skills: dict, bosses: dict):
        self.player_name = player_name
        self.timestamp = timestamp
        self.skills = skills # A dictionary of Skill objects
        self.bosses = bosses # A dictionary of Boss objects

def get_player_stats(player_name):
    """
    Fetches and parses all player stats from the TempleOSRS API's JSON response.
    Returns a PlayerStats object or None if the player isn't found.
    """
    url = f"https://templeosrs.com/api/player_stats.php?player={player_name}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # The API now returns a JSON object. We use .json() to parse it.
        data = response.json()

        # Check if the API returned an error or empty data
        if 'error' in data or not data.get('data'):
            return None

        player_info = data['data']['info']
        player_data = data['data']
        
        # --- Parse Skills ---
        parsed_skills = {}
        skill_names = [
            'Overall', 'Attack', 'Defence', 'Strength', 'Hitpoints', 'Ranged', 'Prayer',
            'Magic', 'Cooking', 'Woodcutting', 'Fletching', 'Fishing', 'Firemaking',
            'Crafting', 'Smithing', 'Mining', 'Herblore', 'Agility', 'Thieving',
            'Slayer', 'Farming', 'Runecraft', 'Hunter', 'Construction'
        ]

        for skill_name in skill_names:
            skill_key = skill_name.lower()
            if skill_name in player_data:
                # Use .get() with a default value to prevent KeyErrors
                rank = player_data.get(f'{skill_name}_rank', 0)
                level = player_data.get(f'{skill_name}_level', 0)
                xp = player_data.get(skill_name, 0)
                
                parsed_skills[skill_key] = Skill(rank=rank, level=level, xp=xp)
            
        # --- Boss parsing is no longer needed if the API doesn't provide it in the same way ---
        # The provided response does not have separate boss entries.
        parsed_bosses = {}


        # Create and return a PlayerStats object
        return PlayerStats(
            player_name=player_info['Username'],
            timestamp=player_info['Last checked'],
            skills=parsed_skills,
            bosses=parsed_bosses,
        )

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {player_name}: {e}")
        return None
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error parsing JSON data for {player_name}: {e}")
        return None