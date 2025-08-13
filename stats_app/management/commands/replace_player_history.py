from django.core.management.base import BaseCommand
from stats_app.models import GroupMember, PlayerHistory
import requests
from django.utils import timezone
import time


def rate_limited_requests(requests_per_minute):
    interval = 60.0 / requests_per_minute
    last_time = [0.0]

    def wait():
        elapsed = time.time() - last_time[0]
        if elapsed < interval:
            time.sleep(interval - elapsed)
        last_time[0] = time.time()

    return wait


class Command(BaseCommand):
    help = "Replace PlayerHistory for a player by fetching all datapoints from TempleOSRS (max 5 requests/minute)"

    def add_arguments(self, parser):
        parser.add_argument("player_name", type=str, help="The RSN of the player")

    def handle(self, *args, **options):
        player_name = options["player_name"]
        try:
            member = GroupMember.objects.get(player_name=player_name)
        except GroupMember.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"Player '{player_name}' not found in GroupMember.")
            )
            return

        # 1. Get all timestamps
        datapoints_url = (
            f"https://templeosrs.com/api/player_datapoints.php?player={player_name}"
        )
        resp = requests.get(datapoints_url)
        if not resp.ok:
            self.stdout.write(
                self.style.ERROR("Failed to fetch datapoints from TempleOSRS.")
            )
            return
        timestamps = resp.json()
        if not timestamps:
            self.stdout.write(
                self.style.WARNING("No datapoints found for this player.")
            )
            return

        # 2. Delete existing PlayerHistory for this player
        PlayerHistory.objects.filter(group_member=member).delete()
        self.stdout.write(
            self.style.SUCCESS(f"Deleted existing PlayerHistory for {player_name}.")
        )

        # 3. Fetch and create new PlayerHistory entries (rate limited)
        created_count = 0
        wait = rate_limited_requests(5)  # 5 requests per minute

        for i, ts in enumerate(timestamps):
            wait()  # Wait if needed to respect rate limit
            stats_url = f"https://templeosrs.com/api/player_stats.php?player={player_name}&date={ts}&bosses=1"
            stats_resp = requests.get(stats_url)
            if stats_resp.ok:
                data = stats_resp.json()
                dt = timezone.datetime.fromtimestamp(ts, tz=timezone.utc)
                PlayerHistory.objects.create(
                    group_member=member, timestamp=dt, data=data
                )
                created_count += 1
                self.stdout.write(f"Added datapoint {i + 1}/{len(timestamps)} ({dt})")
            else:
                self.stdout.write(
                    self.style.WARNING(f"Failed to fetch stats for timestamp {ts}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {created_count} PlayerHistory entries for {player_name}."
            )
        )
