# stats_app/models.py

from django.db import models


class GroupMember(models.Model):
    player_name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.player_name


class PlayerStatsCache(models.Model):
    group_member = models.ForeignKey(GroupMember, on_delete=models.CASCADE)
    data = models.JSONField()
    timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Stats for {self.group_member.player_name} updated on {self.timestamp}"
