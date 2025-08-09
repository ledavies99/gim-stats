import pytest
import json
import datetime
from requests.exceptions import RequestException

import sys
import types

# --- Mock Django models and timezone ---
mock_models = types.ModuleType("stats_app.models")

class MockGroupMember:
    class DoesNotExist(Exception): pass
    class Objects:
        @staticmethod
        def get(player_name=None):
            if player_name == "TestPlayer":
                return MockGroupMember()
            raise MockGroupMember.DoesNotExist()
    objects = Objects()

class MockPlayerStatsCache:
    class DoesNotExist(Exception): pass

    class Objects:
        @staticmethod
        def get(group_member=None):
            # Always raise DoesNotExist to simulate no cache
            raise MockPlayerStatsCache.DoesNotExist()
        @staticmethod
        def create(group_member=None, data=None):
            cache = MockPlayerStatsCache()
            cache.timestamp = datetime.datetime.now()
            cache.data = data
            return cache

    objects = Objects()

    def __init__(self):
        self.timestamp = None
        self.data = None

mock_models.GroupMember = MockGroupMember
mock_models.PlayerStatsCache = MockPlayerStatsCache

sys.modules["stats_app.models"] = mock_models

from stats_app.api_handler import get_player_stats, PlayerStats

class MockResponse:
    def __init__(self, json_data=None, raise_for_status=None, json_side_effect=None):
        self._json_data = json_data
        self._json_side_effect = json_side_effect
        self._raise_for_status = raise_for_status

    def json(self):
        if self._json_side_effect:
            raise self._json_side_effect
        return self._json_data

    def raise_for_status(self):
        if self._raise_for_status:
            raise self._raise_for_status

def test_get_player_stats_success(monkeypatch):
    mock_json = {
        'data': {
            'info': {
                'Username': 'TestPlayer',
                'Last checked': '2024-06-01 12:00:00'
            },
            'Overall': 123456,
            'Overall_rank': 1,
            'Overall_level': 99,
            'Attack': 654321,
            'Attack_rank': 2,
            'Attack_level': 99,
        }
    }
    def mock_get(*args, **kwargs):
        return MockResponse(json_data=mock_json)
    monkeypatch.setattr('stats_app.api_handler.requests.get', mock_get)

    stats = get_player_stats('TestPlayer')
    assert isinstance(stats, PlayerStats)
    assert stats.player_name == 'TestPlayer'
    assert stats.timestamp == '2024-06-01 12:00:00'
    assert 'overall' in stats.skills
    assert stats.skills['overall'].rank == 1
    assert stats.skills['overall'].level == 99
    assert stats.skills['overall'].xp == 123456
    assert 'attack' in stats.skills
    assert stats.skills['attack'].rank == 2
    assert stats.skills['attack'].level == 99
    assert stats.skills['attack'].xp == 654321
    assert stats.bosses["wintertodt"] is not None  # Assuming bosses are always present

def test_get_player_stats_error(monkeypatch):
    mock_json = {'error': 'Player not found'}
    def mock_get(*args, **kwargs):
        return MockResponse(json_data=mock_json)
    monkeypatch.setattr('stats_app.api_handler.requests.get', mock_get)

    stats = get_player_stats('UnknownPlayer')
    assert stats is None

def test_get_player_stats_network_error(monkeypatch):
    def mock_get(*args, **kwargs):
        raise RequestException("Network error")
    monkeypatch.setattr('stats_app.api_handler.requests.get', mock_get)

    stats = get_player_stats('AnyPlayer')
    assert stats is None

def test_get_player_stats_json_decode_error(monkeypatch):
    def mock_get(*args, **kwargs):
        return MockResponse(json_side_effect=json.JSONDecodeError("Expecting value", "", 0))
    monkeypatch.setattr('stats_app.api_handler.requests.get', mock_get)

    stats = get_player_stats('AnyPlayer')
    assert stats is None