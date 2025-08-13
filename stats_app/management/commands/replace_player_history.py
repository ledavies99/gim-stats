from django.core.management.base import BaseCommand
from stats_app.models import GroupMember, PlayerHistory
import requests
from datetime import datetime, timezone


class Command(BaseCommand):
    help = "Replace PlayerHistory for a player by fetching all datapoints from TempleOSRS (up to 200 datapoints)"

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

        # 1. Get all datapoints (up to 200) for the player
        datapoints_url = f"https://templeosrs.com/api/player_datapoints.php?player={player_name}&time=10000000000"
        resp = requests.get(datapoints_url)
        if not resp.ok:
            self.stdout.write(
                self.style.ERROR("Failed to fetch datapoints from TempleOSRS.")
            )
            return
        datapoints = resp.json()
        print(
            f"API response keys: {list(datapoints.get('data', {}).keys())}"
        )  # <--- Add this line

        # Handle API error response
        if isinstance(datapoints, dict) and "error" in datapoints:
            self.stdout.write(self.style.ERROR(f"API error: {datapoints['error']}"))
            return
        if not datapoints:
            self.stdout.write(
                self.style.WARNING("No datapoints found for this player.")
            )
            return

        # 2. Delete existing PlayerHistory for this player
        PlayerHistory.objects.filter(group_member=member).delete()
        self.stdout.write(
            self.style.SUCCESS(f"Deleted existing PlayerHistory for {player_name}.")
        )

        # 3. Create new PlayerHistory entries from datapoints
        created_count = 0
        data_points = datapoints.get("data", {})
        for i, (timestamp_str, stats) in enumerate(sorted(data_points.items())):
            try:
                # Filter: skip if any skill (excluding _ehp and non-numeric) is 0
                has_zero_skill = False
                for k, v in stats.items():
                    if (
                        isinstance(v, (int, float))
                        and not k.endswith("_ehp")
                        and k != "date"
                        and v == 0
                    ):
                        has_zero_skill = True
                        break
                if has_zero_skill:
                    continue

                dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").replace(
                    tzinfo=timezone.utc
                )
                stats_with_date = dict(stats)
                stats_with_date["date"] = timestamp_str

                PlayerHistory.objects.create(
                    group_member=member, timestamp=dt, data={"data": stats_with_date}
                )
                created_count += 1
                self.stdout.write(f"Added datapoint {i + 1}/{len(data_points)} ({dt})")
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"Failed to process datapoint {i + 1}: {e}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {created_count} PlayerHistory entries for {player_name}."
            )
        )
