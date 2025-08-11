# stats_app/management/commands/refresh_cache.py

from django.core.management.base import BaseCommand
from stats_app.models import GroupMember
from stats_app.api_handler import refresh_player_cache


class Command(BaseCommand):
    help = "Refreshes the player stats cache from the API."

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting cache refresh process...")
        players = GroupMember.objects.all()
        self.stdout.write(f"Found {len(players)} players to update.")

        success_count = 0
        fail_count = 0

        for player in players:
            self.stdout.write(f"Refreshing stats for {player.player_name}...")
            if refresh_player_cache(player.player_name):
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully updated {player.player_name}.")
                )
                success_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Failed to update {player.player_name} (rate-limited or error)."
                    )
                )
                fail_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Cache refresh process completed. Success: {success_count}, Failed: {fail_count}"
            )
        )
