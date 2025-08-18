from django.core.management.base import BaseCommand
from stats_app.models import GroupMember, PlayerHistory
from stats_app.api_handler import load_config, carry_forward
import requests
from datetime import datetime, timezone


def xp_to_level(xp):
    lvl_xp = 0
    for level in range(1, 127):  # 126 is max
        lvl_xp += int((level + 300 * 2 ** (level / 7)) // 4)
        if lvl_xp > xp:
            return level
    return 126


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

        config = load_config()
        skill_names = config.get("skills", [])

        # 1. Get all datapoints (up to 200) for the player
        datapoints_url = f"https://templeosrs.com/api/player_datapoints.php?player={player_name}&time=10000000000"
        resp = requests.get(datapoints_url)
        if not resp.ok:
            self.stdout.write(
                self.style.ERROR("Failed to fetch datapoints from TempleOSRS.")
            )
            return
        datapoints = resp.json()

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

        # Carry forward previous values for missing skills
        previous_xp = {skill: 0 for skill in skill_names}

        for i, (timestamp_str, stats) in enumerate(sorted(data_points.items())):
            stats_with_date = dict(stats)
            stats_with_date["date"] = timestamp_str

            for skill in skill_names:
                xp = carry_forward(stats.get(skill), previous_xp.get(skill, 0))
                previous_xp[skill] = xp
                stats_with_date[skill] = xp

            try:
                dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").replace(
                    tzinfo=timezone.utc
                )

                # Add level fields for each skill and sum for overall
                overall_level = 0
                for skill in skill_names:
                    if skill.lower() == "overall":
                        continue  # Skip the "Overall" skill
                    xp = stats_with_date.get(skill, 0)
                    level = xp_to_level(xp)
                    stats_with_date[f"{skill}_level"] = level
                    overall_level += level
                stats_with_date["Overall_level"] = overall_level

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
