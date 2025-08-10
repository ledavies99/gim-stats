# stats_app/admin.py

from django.contrib import admin
from .models import GroupMember, PlayerStatsCache, APICallLog


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ("player_name",)


@admin.register(PlayerStatsCache)
class PlayerStatsCacheAdmin(admin.ModelAdmin):
    list_display = ("group_member", "last_updated")


@admin.register(APICallLog)
class APICallLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp",)
