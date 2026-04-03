from django.urls import path

from .views import LeaderboardView, LoginView, QuizView, SubmitResultView

urlpatterns = [
    path('quiz/', QuizView.as_view(), name='quiz'),
    path('quiz/submit/', SubmitResultView.as_view(), name='submit'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
]
