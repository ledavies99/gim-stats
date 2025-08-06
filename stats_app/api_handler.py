# stats_app/api_handler.py

import requests

def get_player_stats(player_name):
    """
    Fetches and parses all player stats from the TempleOSRS API.
    Returns a dictionary of stats or None if the player isn't found.
    """
    url = f"https://templeosrs.com/api/player_stats.php?player={player_name}"

    try:
        response = requests.get(url)
        response.raise_for_status()

        # The API returns a long CSV string.
        data_list = response.text.split(',')
        
        # A simple check to ensure the response is not empty or malformed.
        if len(data_list) < 25: # Minimal number of fields for a basic response
            return None

        # Helper function to parse skill data blocks (rank, level, xp)
        def parse_skill_block(index):
            return {
                'rank': int(data_list[index]),
                'level': int(data_list[index + 1]),
                'xp': int(data_list[index + 2]),
            }
        
        # Helper function to parse boss data blocks (rank, killcount)
        def parse_boss_block(index):
            return {
                'rank': int(data_list[index]),
                'killcount': int(data_list[index + 1]),
            }

        # The full list of skills and their starting index in the CSV response
        # NOTE: You MUST verify these indices with the latest TempleOSRS API documentation.
        # This is based on a common structure but could change.
        skills_and_indices = {
            'overall': 2,
            'attack': 5,
            'defence': 8,
            'strength': 11,
            'hitpoints': 14,
            'ranged': 17,
            'prayer': 20,
            'magic': 23,
            'cooking': 26,
            'woodcutting': 29,
            'fletching': 32,
            'fishing': 35,
            'firemaking': 38,
            'crafting': 41,
            'smithing': 44,
            'mining': 47,
            'herblore': 50,
            'agility': 53,
            'thieving': 56,
            'slayer': 59,
            'farming': 62,
            'runecrafting': 65,
            'hunter': 68,
            'construction': 71,
        }

        # The full list of bosses and their starting index
        bosses_and_indices = {
            'abyssal_sire': 74,
            'alchemical_hydra': 77,
            'barrows_chests': 80,
            'bryophyta': 83,
            # ... continue for all bosses you want to track
        }
        
        # Start building the final data dictionary
        stats_data = {
            'player_name': data_list[0],
            'timestamp': data_list[1],
            'skills': {},
            'bosses': {},
        }

        # Parse skills
        for skill_name, index in skills_and_indices.items():
            # Skill data is (rank, level, xp)
            stats_data['skills'][skill_name] = parse_skill_block(index)

        # Parse bosses
        for boss_name, index in bosses_and_indices.items():
            # Boss data is (rank, killcount, EHP)
            stats_data['bosses'][boss_name] = {
                'rank': int(data_list[index]),
                'killcount': int(data_list[index + 1]),
            }
        
        return stats_data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {player_name}: {e}")
        return None
    except (IndexError, ValueError) as e:
        # Catch errors if the API response is malformed or indices are wrong
        print(f"Error parsing data for {player_name}: {e}")
        return None