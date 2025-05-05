from django.urls import path
from .views import (
    SignUpView, LoginView, DashboardView, LogoutView, ResetPasswordView, ResetPasswordConfirmView , LeagueFixturesPredictionView
)

urlpatterns = [
    path('register/',SignUpView.as_view(), name='signup'),
    path('login/',LoginView.as_view(), name='login'),
    
    path('dashboard/',DashboardView.as_view(), name='dashboard'),
    
    path('logout/', LogoutView.as_view(), name='logout'),
    
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('reset-password/<str:token>/', ResetPasswordConfirmView.as_view(), name='reset-password'),
    
    path('league/<int:pk>/fixtures/', LeagueFixturesPredictionView.as_view(), name='league-fixtures'),

    
]
