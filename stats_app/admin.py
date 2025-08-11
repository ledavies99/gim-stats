from django.contrib import admin
from .models import GroupMember, PlayerStatsCache, APICallLog, PlayerHistory

# Register your models here.


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = (
        "player_name",
        "in_group",
    )
    search_fields = ("player_name",)


@admin.register(PlayerStatsCache)
class PlayerStatsCacheAdmin(admin.ModelAdmin):
    list_display = (
        "group_member",
        "last_updated",
    )
    search_fields = ("group_member__player_name",)


@admin.register(APICallLog)
class APICallLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp",)


@admin.register(PlayerHistory)
class PlayerHistoryAdmin(admin.ModelAdmin):
    """
    Admin configuration for the PlayerHistory model.
    This makes the historical data viewable and searchable in the Django admin.
    """

    list_display = (
        "group_member",
        "timestamp",
    )
    search_fields = ("group_member__player_name",)
    list_filter = ("timestamp",)
