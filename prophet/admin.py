from django.contrib import admin
from .models import (
    Country, League, Team, Fixture,
    HeadToHead, TeamStat, PredictionType,
    Prediction, Gambler, System_User, PasswordResetToken,
    Player, SuspendedPlayer, InjuredPlayer, TeamForm, PredictedResult
)

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

@admin.register(League)
class LeagueAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'country')
    list_filter = ('country',)
    search_fields = ('name',)

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'league')
    list_filter = ('league',)
    search_fields = ('name',)

@admin.register(Fixture)
class FixtureAdmin(admin.ModelAdmin):
    list_display = ('id', 'league', 'home_team', 'away_team', 'date', 'time')
    list_filter = ('league',)
    search_fields = ('home_team', 'away_team')

@admin.register(HeadToHead)
class HeadToHeadAdmin(admin.ModelAdmin):
    list_display = ('id', 'fixture', 'match_date', 'result')
    list_filter = ('fixture',)
    search_fields = ('match_date', 'result')

@admin.register(TeamStat)
class TeamStatAdmin(admin.ModelAdmin):
    list_display = ('id', 'fixture', 'team')
    list_filter = ('fixture',)
    search_fields = ('team',)
    
@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_filter = ('name',)
    search_fields = ('name',)

@admin.register(SuspendedPlayer)
class SuspendedPlayerAdmin(admin.ModelAdmin):
    list_display = ('player',)
    list_filter = ('player',)
    search_fields = ('player',)
    
@admin.register(InjuredPlayer)
class InjuredPlayerAdmin(admin.ModelAdmin):
    list_display = ('player',)
    list_filter = ('player',)
    search_fields = ('player',)

@admin.register(TeamForm)
class TeamFormAdmin(admin.ModelAdmin):
    list_display = ('team', 'fixture', 'game_number', 'result', 'over_under', 'gg')
    list_filter = ('team', 'fixture')
    search_fields = ('team', 'fixture')

@admin.register(PredictionType)
class PredictionTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_filter = ('name',)
    search_fields = ('name',)

@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ('id', 'fixture', 'prediction_type', 'value', 'prediction_site', 'site_accuracy', 'team_effort')
    list_filter = ('fixture', 'team_effort')
    search_fields = ('prediction_site', 'site_accuracy', 'team_effort')

@admin.register(PredictedResult)
class PredictedResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'fixture', 'home_team', 'away_team', 'prediction_type', 'predicted_result', 'created_at')
    list_filter = ('fixture', 'home_team', 'away_team', 'prediction_type')
    search_fields = ('predicted_result',)

@admin.register(Gambler)
class GamblerAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'email_address', 'phone_number')
    list_filter = ('email_address',)
    search_fields = ('email_address', 'phone_number')

@admin.register(System_User)
class System_UserAdmin(admin.ModelAdmin):
    list_display = ('username',)
    list_filter = ('username',)
    search_fields = ('username',)

@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('username', 'token')
    list_filter = ('username', 'token',)
    search_fields = ('username', 'token', 'created_at')
