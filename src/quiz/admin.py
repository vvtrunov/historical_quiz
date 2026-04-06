from django.contrib import admin

from .models import Event, Player, QuizResult


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('year', 'month', 'day', 'short_description')
    list_filter = ('month',)
    search_fields = ('description',)
    ordering = ('month', 'day', 'year')

    @admin.display(description='Description')
    def short_description(self, obj):
        return obj.description[:80]


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('token', 'created_at')


@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
    list_display = ('player', 'date', 'score', 'total', 'played_at')
    list_filter = ('date',)
    search_fields = ('player__name',)
    readonly_fields = ('played_at',)
