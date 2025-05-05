from django.db import models
from datetime import date
from django.utils import timezone
import random
import string
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password, check_password
from .validators import validate_kenyan_phone_number
from django.core.validators import MinValueValidator, MaxValueValidator


class Country(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class League(models.Model):
    id = models.AutoField(primary_key=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='leagues')
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.country.name})"


class Team(models.Model):
    id = models.AutoField(primary_key=True)
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='teams')
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Fixture(models.Model):
    id = models.AutoField(primary_key=True)
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='fixtures')
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_fixtures')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_fixtures')
    date = models.DateField()
    time = models.TimeField()

    def __str__(self):
        return f"{self.home_team.name} vs {self.away_team.name} - {self.date}"


class HeadToHead(models.Model):
    id = models.AutoField(primary_key=True)
    fixture = models.ForeignKey(Fixture, on_delete=models.CASCADE, related_name='head_to_heads')
    match_date = models.DateField()
    result = models.CharField(max_length=50)  # example: "2-1", "1-1"

    def __str__(self):
        return f"H2H {self.fixture}: {self.result}"


class TeamStat(models.Model):
    id = models.AutoField(primary_key=True)
    fixture = models.ForeignKey(Fixture, on_delete=models.CASCADE, related_name='team_stats')
    team = models.ForeignKey(Team, on_delete=models.CASCADE)

    def __str__(self):
        return f"Stats: {self.team.name} - {self.fixture}"

class Player(models.Model):
    POSITION_CHOICES = [
        ('GK', 'Goalkeeper'),
        ('CB', 'Central Defence'),
        ('WB', 'Wing Defence'),
        ('DM', 'Defensive Midfield'),
        ('AM', 'Attacking Midfield'),
        ('WG', 'Winger'),
        ('ST', 'Striker'),
    ]

    EFFECT_CHOICES = [
        ('threat', 'Threat'),
        ('best', 'Best'),
        ('moderate', 'Moderate'),
        ('required', 'Required'),
    ]

    id = models.AutoField(primary_key=True)
    player_code = models.CharField(max_length=10, unique=True)  # Example: 'PLY001'
    team = models.ForeignKey('Team', on_delete=models.CASCADE, related_name='players')
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=20, choices=POSITION_CHOICES)
    effect = models.CharField(max_length=20, choices=EFFECT_CHOICES)
    rating = models.PositiveIntegerField(default=0)  # Rating out of 100

    def __str__(self):
        return f"{self.name} ({self.position}) - {self.player_code}"

class SuspendedPlayer(models.Model):
    player = models.OneToOneField(Player, on_delete=models.CASCADE, related_name='suspension')

    def __str__(self):
        return f"Suspended: {self.player.name}"
    
class InjuredPlayer(models.Model):
    player = models.OneToOneField(Player, on_delete=models.CASCADE, related_name='injury')

    def __str__(self):
        return f"Injured: {self.player.name}"

class TeamForm(models.Model):
    RESULT_CHOICES = [
        ('W', 'Win'),
        ('D', 'Draw'),
        ('L', 'Loss'),
    ]

    OVER_UNDER_CHOICES = [
        ('Over', 'Over'),
        ('Under', 'Under'),
    ]

    GG_CHOICES = [
        ('gg', 'GG'),
        ('no gg', 'No GG'),
    ]

    id = models.AutoField(primary_key=True)
    team = models.ForeignKey('Team', on_delete=models.CASCADE, related_name='forms')
    fixture = models.ForeignKey('Fixture', on_delete=models.CASCADE, related_name='forms')
    game_number = models.PositiveIntegerField()  # 1 to 5
    result = models.CharField(max_length=1, choices=RESULT_CHOICES)
    over_under = models.CharField(max_length=5, choices=OVER_UNDER_CHOICES)
    gg = models.CharField(max_length=5, choices=GG_CHOICES)

    def __str__(self):
        return f"Form {self.game_number} - {self.team.name}"

class PredictionType(models.Model):
    PREDICTION_CHOICES = [
        ('1X2', '1X2'),
        ('GG', 'GG'),
        ('Over', 'Over'),
        ('Under', 'Under'),
        ('Handicap', 'Handicap'),
        ('Correct Score', 'Correct Score'),
    ]

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, choices=PREDICTION_CHOICES)

    def __str__(self):
        return self.name



class Prediction(models.Model):
    EFFORT_CHOICES = [
        ('none', 'No Motivation'),  # team not fighting for anything
        ('survival', 'Fighting Relegation'),
        ('promotion', 'Fighting Promotion'),
        ('title', 'Fighting for Title'),
        ('qualification', 'Fighting for Qualification'),
        ('rivalry', 'Playing Rivalry Game'),
    ]

    id = models.AutoField(primary_key=True)
    fixture = models.ForeignKey(Fixture, on_delete=models.CASCADE, related_name='predictions')
    prediction_type = models.ForeignKey(PredictionType, on_delete=models.CASCADE)
    value = models.CharField(max_length=100)  # e.g., "1", "GG", "Over 2.5", "2-1"
    prediction_site = models.CharField(max_length=100)
    site_accuracy = models.DecimalField(max_digits=5, decimal_places=2)  # e.g., 85.75%
    team_effort = models.CharField(max_length=20, choices=EFFORT_CHOICES, default='none')

    def __str__(self):
        return f"{self.fixture}: {self.prediction_type} - {self.value} ({self.team_effort}) from {self.prediction_site}"

class PredictedResult(models.Model):
    id = models.AutoField(primary_key=True)
    fixture = models.ForeignKey(Fixture, on_delete=models.CASCADE, related_name='predicted_results')
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_predictions')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_predictions')
    prediction_type = models.ForeignKey(PredictionType, on_delete=models.CASCADE)
    predicted_result = models.CharField(max_length=100)  # e.g., "1", "2-1", "GG", "Over 2.5"
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.fixture}: {self.prediction_type} - {self.predicted_result}"

    
class Gambler(models.Model):
    id = models.AutoField(primary_key=True)
    email_address = models.EmailField(max_length=200, help_text="Please Enter Lecturer Email Address")
    username = models.EmailField(unique=True, max_length=200, help_text="Enter a valid Username")
    first_name = models.CharField(max_length=200, help_text="Please Enter Student First Name")
    last_name = models.CharField(max_length=200, help_text="Please Enter Student Last Name")
    phone_number = models.CharField(max_length=13, validators=[validate_kenyan_phone_number], help_text="Enter phone number in the format 0798073204 or +254798073404")

    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class System_User(models.Model):
    username = models.CharField(primary_key=True, unique=True, max_length=50, help_text="Enter a valid Username")
    password_hash = models.CharField(max_length=128, help_text="Enter a valid password")  # Store hashed password

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)

    def clean(self):
        # Custom validation for password field
        if len(self.password_hash) < 8:
            raise ValidationError("Password must be at least 8 characters long.")

    def __str__(self):
        return self.username   

class PasswordResetToken(models.Model):
    username = models.ForeignKey(System_User, on_delete=models.CASCADE)
    token = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Token for {self.username}"

    def is_expired(self):
        expiration_time = self.created_at + timedelta(minutes=5)
        return timezone.now() > expiration_time
