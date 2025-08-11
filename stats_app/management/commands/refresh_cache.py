# stats_app/management/commands/refresh_cache.py

from django.core.management.base import BaseCommand
from stats_app.models import GroupMember, PlayerStatsCache
from stats_app.api_handler import get_player_stats


class Command(BaseCommand):
    help = "Clears and refreshes the player stats cache."

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting cache refresh process...")

        self.stdout.write("Clearing existing PlayerStatsCache...")
        count, _ = PlayerStatsCache.objects.all().delete()
        self.stdout.write(
            self.style.SUCCESS(f"Successfully deleted {count} old cache records.")
        )

        players = GroupMember.objects.all()
        self.stdout.write(f"Found {len(players)} players to update.")

        for player in players:
            self.stdout.write(f"Refreshing stats for {player.player_name}...")
            try:
                get_player_stats(player.player_name)
            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(f"Failed for {player.player_name}: {e}")
                )

        self.stdout.write(
            self.style.SUCCESS("Cache refresh process completed successfully!")
        )
