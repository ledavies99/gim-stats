# stats_app/models.py

from django.db import models

class GroupMember(models.Model):
    player_name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.player_name