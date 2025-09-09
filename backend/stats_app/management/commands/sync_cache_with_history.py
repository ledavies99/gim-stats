from django.core.management.base import BaseCommand
from stats_app.models import GroupMember, PlayerHistory, PlayerStatsCache
from stats_app.api_handler import load_config
import requests


class Command(BaseCommand):
    help = "Sync PlayerStatsCache to the latest PlayerHistory for a specific player, merging in boss data."

    def add_arguments(self, parser):
        parser.add_argument("player_name", type=str, help="The RSN of the player")

    def handle(self, *args, **options):
        player_name = options["player_name"]
        try:
            member = GroupMember.objects.get(player_name=player_name)
        except GroupMember.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Player '{player_name}' not found."))
            return

        latest = (
            PlayerHistory.objects.filter(group_member=member)
            .order_by("-timestamp")
            .first()
        )
        if not latest:
            self.stdout.write(self.style.WARNING(f"No history for {player_name}"))
            return

        # Extract timestamp string in the format used by TempleOSRS
        timestamp_str = latest.timestamp.strftime("%Y-%m-%d %H:%M:%S")

        # Fetch boss data for this timestamp
        bosses_url = (
            f"https://templeosrs.com/api/player_datapoints.php?player={player_name}"
            f"&time=10000000000&bosses=1"
        )
        resp = requests.get(bosses_url)
        if not resp.ok:
            self.stdout.write(
                self.style.ERROR("Failed to fetch boss datapoints from TempleOSRS.")
            )
            return
        boss_datapoints = resp.json().get("data", {})
        boss_data = boss_datapoints.get(timestamp_str, {})

        # Merge skill data (from PlayerHistory) and boss data (from API)
        merged_data = dict(latest.data.get("data", {}))  # skills and meta
        merged_data.update(boss_data)  # add/overwrite with boss data

        # Ensure all boss keys from config are present (even if 0)
        config = load_config()
        for boss in config.get("bosses", []):
            if boss not in merged_data:
                merged_data[boss] = 0

        # Save to PlayerStatsCache
        cache, _ = PlayerStatsCache.objects.get_or_create(group_member=member)
        cache.data = {"data": merged_data}
        cache.last_updated = latest.timestamp
        cache.save()
        self.stdout.write(self.style.SUCCESS(f"Updated cache for {member.player_name}"))
