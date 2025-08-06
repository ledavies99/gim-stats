# stats_app/admin.py

from django.contrib import admin
from .models import GroupMember, PlayerStatsCache

admin.site.register(GroupMember)
admin.site.register(PlayerStatsCache)