import sys
import types
import json
import pytest
from requests.exceptions import RequestException, HTTPError

# --- Mock Django models ---
mock_models = types.ModuleType("stats_app.models")


class MockGroupMember:
    pass


class MockPlayerStatsCache:
    pass


class MockGroupMemberDoesNotExist(Exception):
    pass


class MockPlayerStatsCacheDoesNotExist(Exception):
    pass


class MockGroupMemberObjects:
    @staticmethod
    def get(player_name=None):
        if player_name == "TestPlayer":
            return MockGroupMember()
        raise MockGroupMemberDoesNotExist()


class MockPlayerStatsCacheObjects:
    @staticmethod
    def get(group_member=None):
        raise MockPlayerStatsCacheDoesNotExist()

    @staticmethod
    def create(group_member=None, data=None):
        cache = MockPlayerStatsCache()
        cache.timestamp = None
        cache.data = data
        return cache


MockGroupMember.DoesNotExist = MockGroupMemberDoesNotExist
MockGroupMember.objects = MockGroupMemberObjects()
MockPlayerStatsCache.DoesNotExist = MockPlayerStatsCacheDoesNotExist
MockPlayerStatsCache.objects = MockPlayerStatsCacheObjects()

mock_models.GroupMember = MockGroupMember
mock_models.PlayerStatsCache = MockPlayerStatsCache

sys.modules["stats_app.models"] = mock_models

from stats_app.api_handler import (  # noqa: E402
    get_player_stats,
    PlayerStats,
    fetch_player_stats_from_api,
)


# --- Shared MockResponse for requests.get ---
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


@pytest.fixture
def monkeypatch_requests(monkeypatch):
    def _patch(response):
        monkeypatch.setattr(
            "stats_app.api_handler.requests.get", lambda *a, **k: response
        )

    return _patch


@pytest.fixture
def mock_config(monkeypatch):
    # Patch load_config to always return these skills/bosses for deterministic tests
    config = {
        "skills": ["Overall", "Attack"],
        "bosses": ["Wintertodt"],
    }
    monkeypatch.setattr("stats_app.api_handler.load_config", lambda: config)


def test_get_player_stats_success(monkeypatch, mock_config):
    """Test get_player_stats returns correct PlayerStats object on success."""
    mock_json = {
        "data": {
            "info": {"Username": "TestPlayer", "Last checked": "2024-06-01 12:00:00"},
            "Overall": 123456,
            "Overall_rank": 1,
            "Overall_level": 99,
            "Attack": 654321,
            "Attack_rank": 2,
            "Attack_level": 99,
            "Wintertodt": 42,
        }
    }
    monkeypatch.setattr(
        "stats_app.api_handler.requests.get",
        lambda *a, **k: MockResponse(json_data=mock_json),
    )
    stats = get_player_stats("TestPlayer")
    assert isinstance(stats, PlayerStats)
    assert stats.player_name == "TestPlayer"
    assert stats.timestamp == "2024-06-01 12:00:00"
    assert "overall" in stats.skills
    assert stats.skills["overall"].rank == 1
    assert stats.skills["overall"].level == 99
    assert stats.skills["overall"].xp == 123456
    assert "attack" in stats.skills
    assert stats.skills["attack"].rank == 2
    assert stats.skills["attack"].level == 99
    assert stats.skills["attack"].xp == 654321
    assert "wintertodt" in stats.bosses
    assert stats.bosses["wintertodt"].killcount == 42


def test_get_player_stats_error(monkeypatch, mock_config):
    """Test get_player_stats returns None if player not found."""
    stats = get_player_stats("UnknownPlayer")
    assert stats is None


def test_get_player_stats_network_error(monkeypatch, mock_config):
    """Test get_player_stats returns None on network error."""
    monkeypatch.setattr(
        "stats_app.api_handler.requests.get",
        lambda *a, **k: (_ for _ in ()).throw(RequestException("Network error")),
    )
    stats = get_player_stats("TestPlayer")
    assert stats is None


def test_get_player_stats_json_decode_error(monkeypatch, mock_config):
    """Test get_player_stats returns None on JSON decode error."""
    monkeypatch.setattr(
        "stats_app.api_handler.requests.get",
        lambda *a, **k: MockResponse(
            json_side_effect=json.JSONDecodeError("Expecting value", "", 0)
        ),
    )
    stats = get_player_stats("TestPlayer")
    assert stats is None


def test_fetch_player_stats_from_api_success(monkeypatch):
    """Test fetch_player_stats_from_api returns JSON on success."""
    expected_json = {"data": {"info": {"Username": "TestPlayer"}}}
    monkeypatch.setattr(
        "stats_app.api_handler.requests.get",
        lambda url: MockResponse(json_data=expected_json),
    )
    result = fetch_player_stats_from_api("TestPlayer")
    assert result == expected_json


@pytest.mark.parametrize(
    "raise_exc,exc_type",
    [
        (RequestException("HTTP error"), RequestException),
        (HTTPError("Bad status code"), HTTPError),
    ],
)
def test_fetch_player_stats_from_api_errors(monkeypatch, raise_exc, exc_type):
    """Test fetch_player_stats_from_api raises on HTTP errors."""
    monkeypatch.setattr(
        "stats_app.api_handler.requests.get",
        lambda url: MockResponse(raise_for_status=raise_exc),
    )
    with pytest.raises(exc_type):
        fetch_player_stats_from_api("TestPlayer")


def test_fetch_player_stats_from_api_json_decode_error(monkeypatch):
    """Test fetch_player_stats_from_api raises on JSON decode error."""
    monkeypatch.setattr(
        "stats_app.api_handler.requests.get",
        lambda url: MockResponse(
            json_side_effect=json.JSONDecodeError("Expecting value", "", 0)
        ),
    )
    with pytest.raises(json.JSONDecodeError):
        fetch_player_stats_from_api("TestPlayer")
