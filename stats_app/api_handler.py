# stats_app/api_handler.py

import requests

def get_player_stats(player_name):
    """
    Fetches player stats from the TempleOSRS API.
    Parses the CSV response into a dictionary.
    Returns a dictionary of stats or None if the player isn't found.
    """
    url = f"https://templeosrs.com/api/player_stats.php?player={player_name}"

    try:
        response = requests.get(url)
        response.raise_for_status()

        data_list = response.text.split(',')

        # Quick check for valid response
        if len(data_list) < 50:
            return None

        # Parse info block (first element is a JSON-like string)
        info_raw = data_list[0]
        info_str = info_raw.replace('{"data":{"info":{', '').replace('}}', '')
        info = {}
        for item in info_str.split('","'):
            item = item.replace('"', '')
            if '":"' in item:
                key, value = item.split('":"', 1)
                info[key] = value
            elif ':' in item:
                key, value = item.split(':', 1)
                info[key] = value
            else:
                info[item] = None  # Handle keys with no value

        # Find the index of the date field
        date_idx = None
        for i, item in enumerate(data_list):
            if item.startswith('"date":'):
                date_idx = i
                break
        if date_idx is None:
            print("Date field not found in data_list")
            return None

        # Parse date
        date = data_list[date_idx].replace('"date":"', '').replace('"', '')

        # Overall stats
        overall = {
            'xp': int(data_list[date_idx+1].replace('"Overall":', '')),
            'rank': int(data_list[date_idx+2].replace('"Overall_rank":', '')),
            'level': int(data_list[date_idx+3].replace('"Overall_level":', '')),
            'ehp': float(data_list[date_idx+4].replace('"Overall_ehp":', ''))
        }

        # Skill order and offsets
        skills = [
            'Attack', 'Defence', 'Strength', 'Hitpoints', 'Ranged', 'Prayer', 'Magic',
            'Cooking', 'Woodcutting', 'Fletching', 'Fishing', 'Firemaking', 'Crafting',
            'Smithing', 'Mining', 'Herblore', 'Agility', 'Thieving', 'Slayer',
            'Farming', 'Runecraft', 'Hunter', 'Construction'
        ]
        skills_data = {}
        offset = date_idx + 5
        for skill in skills:
            try:
                xp = int(data_list[offset].replace(f'"{skill}":', ''))
                rank = int(data_list[offset+1].replace(f'"{skill}_rank":', ''))
                level = int(data_list[offset+2].replace(f'"{skill}_level":', ''))
                ehp = float(data_list[offset+3].replace(f'"{skill}_ehp":', ''))
            except Exception as e:
                print(f"Error parsing skill {skill} at offset {offset}: {e}")
                xp, rank, level, ehp = None, None, None, None
            skills_data[skill.lower()] = {
                'xp': xp,
                'rank': rank,
                'level': level,
                'ehp': ehp
            }
            offset += 4

        # EHP and ranks (at the end)
        ehp = float(data_list[offset].replace('"Ehp":', ''))
        ehp_rank = int(data_list[offset+1].replace('"Ehp_rank":', ''))

        stats_data = {
            'info': info,
            'date': date,
            'overall': overall,
            'skills': skills_data,
            'ehp': ehp,
            'ehp_rank': ehp_rank
        }

        return stats_data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {player_name}: {e}")
        return None
    except Exception as e:
        print(f"Error parsing data for {player_name}: {e}")
        return None

stats = get_player_stats('Bogsloppit')  # Example call to test the function
print(stats)  # Print the stats to verify