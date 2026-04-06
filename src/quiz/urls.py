from django.urls import path

from .views import LeaderboardView, LoginView, LogoutView, QuizView, ScoreView

urlpatterns = [
    path('', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('quiz/', QuizView.as_view(), name='quiz'),
    path('score/', ScoreView.as_view(), name='score'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
]
