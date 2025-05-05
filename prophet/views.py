from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth import logout
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.conf import settings
from django.contrib import messages
import re

from .models import Gambler, PasswordResetToken, System_User, Country, Team, Fixture, League
from .forms import SignUpForm, LoginForm, UploadFileForm, ResetForm, PasswordResetForm

from .utils import PredictionEngine

from django.views.generic import TemplateView

class SignUpView(View):
    template_name = 'signup.html'

    def get(self, request):
        return render(request, self.template_name, {'form': SignUpForm()})

    def post(self, request):
        form = SignUpForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password_hash = form.cleaned_data['password_hash']

            if System_User.objects.filter(username=username).exists():
                form.add_error('username', "This username has already been used in the system!")
            elif not self.is_username(username) or not Gambler.objects.filter(username=username).exists():
                form.add_error('username', "Invalid or non-existent gambler email.")
            else:
                new_account = form.save(commit=False)
                new_account.set_password(password_hash)
                new_account.save()
                return redirect('login')
        return render(request, self.template_name, {'form': form})

    def is_username(self, username):
        return bool(re.match(r'^[a-zA-Z0-9]{1,15}@gmail\.com$', username))

class LoginView(View):
    template_name = 'login.html'

    def get(self, request):
        return render(request, self.template_name, {'form': LoginForm()})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            if self.is_username(username):
                user = System_User.objects.filter(username=username).first()
                if user and user.check_password(password):
                    gambler = Gambler.objects.filter(username=username).first()
                    if gambler:
                        request.session['username'] = user.username
                        request.session['email_address'] = gambler.email_address
                        return redirect('dashboard')  # Added redirect after successful login
        return render(request, self.template_name, {'form': form})

    def is_username(self, username):
        return bool(re.match(r'^[a-zA-Z0-9]{1,15}@gmail\.com$', username))

class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('login')

class ResetPasswordView(View):
    template_name = 'reset_password.html'

    def get(self, request):
        return render(request, self.template_name, {'form': PasswordResetForm()})

    def post(self, request):
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            user = System_User.objects.filter(username=username).first()
            if user:
                try:
                    token = get_random_string(length=32)
                    PasswordResetToken.objects.create(username=user, token=token)
                    reset_link = request.build_absolute_uri(f'/reset-password/{token}/')
                    send_mail(
                        'Reset Your Password',
                        f'Click the link to reset your password: {reset_link}',
                        settings.EMAIL_HOST_USER,
                        [user.username],
                        fail_silently=False,
                    )
                    success_message = f"A password reset link has been sent to {user.username}."
                    return render(request, self.template_name, {'form': form, 'success_message': success_message})
                except Exception as e:
                    error_message = f"An error occurred: {str(e)}"
            else:
                error_message = "Email address does not exist in our records."
            return render(request, self.template_name, {'form': form, 'error_message': error_message})
        return render(request, self.template_name, {'form': form})

class ResetPasswordConfirmView(View):
    template_name = 'reset_password_confirm.html'

    def get(self, request, token):
        form = ResetForm()
        token_obj = PasswordResetToken.objects.filter(token=token).first()

        if not token_obj or token_obj.is_expired():
            error_message = "Token is invalid or expired."
            return render(request, self.template_name, {'form': form, 'token': token, 'error_message': error_message})
        return render(request, self.template_name, {'form': form, 'token': token})

    def post(self, request, token):
        form = ResetForm(request.POST)
        token_obj = PasswordResetToken.objects.filter(token=token).first()

        if not token_obj or token_obj.is_expired():
            error_message = "Token is invalid or expired."
            return render(request, self.template_name, {'form': form, 'token': token, 'error_message': error_message})

        if form.is_valid():
            user = get_object_or_404(System_User, username=token_obj.username)
            form.save(user)
            token_obj.delete()
            messages.success(request, "Your password has been reset successfully.")
            return render(request, self.template_name, {'form': form, 'token': token})

        return render(request, self.template_name, {'form': form, 'token': token, 'error_message': "Invalid form submission."})

class DashboardView(View):
    def get(self, request):
        username = request.session.get('username')
        if not username:
            return redirect('login')

        gambler = Gambler.objects.filter(username=username).first()
        if not gambler:
            return redirect('login')

        user = System_User.objects.get(username=username)

        total_countries = Country.objects.count()
        total_teams = Team.objects.count()
        total_fixtures = Fixture.objects.count()

        teams = Team.objects.all()[:5]
        leagues = League.objects.all()[:5]

        context = {
            'last_name': gambler.last_name,
            'user': user,
            'total_countries': total_countries,
            'total_teams': total_teams,
            'total_fixtures': total_fixtures,
            'teams': teams,
            'leagues': leagues,
        }
        return render(request, 'dashboard.html', context)

class LeagueFixturesPredictionView(TemplateView):
    template_name = 'league_fixtures.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        league_id = self.kwargs.get('pk')
        league = get_object_or_404(League, pk=league_id)
        fixtures = Fixture.objects.filter(league=league)

        fixtures_with_predictions = []
        for fixture in fixtures:
            engine = PredictionEngine(fixture_id=fixture.pk)
            fixture_data = {
                'fixture': fixture,
                'prediction_1x2': engine.predict_1x2(),
                'prediction_over_under': engine.predict_over_under(),
                'prediction_gg': engine.predict_gg(),
                'prediction_handicap': engine.predict_handicap(),
                'prediction_correct_score': engine.predict_correct_score(),
            }
            fixtures_with_predictions.append(fixture_data)

        context['league'] = league
        context['fixtures_with_predictions'] = fixtures_with_predictions
        return context

