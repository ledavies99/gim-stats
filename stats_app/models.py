from django.db import models
from django.db.models import JSONField


class GroupMember(models.Model):
    player_name = models.CharField(max_length=50, unique=True)
    in_group = models.BooleanField(default=True)

    def __str__(self):
        return self.player_name


class PlayerStatsCache(models.Model):
    group_member = models.OneToOneField(GroupMember, on_delete=models.CASCADE)
    data = JSONField()
    last_updated = models.DateTimeField(auto_now=True)


class APICallLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)


class PlayerHistory(models.Model):
    """
    Model to store historical snapshots of a player's stats.
    Each entry is a full dump of stats at a specific point in time.
    """

    group_member = models.ForeignKey(GroupMember, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    data = JSONField()

    def __str__(self):
        return f"{self.group_member.player_name} - {self.timestamp}"
