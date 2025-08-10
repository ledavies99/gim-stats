# stats_app/models.py

from django.db import models


class GroupMember(models.Model):
    player_name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.player_name


class PlayerStatsCache(models.Model):
    group_member = models.OneToOneField(GroupMember, on_delete=models.CASCADE)
    data = models.JSONField()
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cache for {self.group_member.player_name}"


class APICallLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"API call at {self.timestamp}"
