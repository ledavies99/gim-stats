import os
import json


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


def load_config():
    """Loads the configuration from a JSON file."""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "config.json")
        with open(config_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def carry_forward(new_value, prev_value):
    """Carry forward the value if it's None or less than the previous value."""
    if new_value is None:
        return prev_value
    if new_value < prev_value:
        return prev_value
    return new_value
