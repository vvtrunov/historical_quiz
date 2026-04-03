from django.urls import path

from .views import LoginView, QuizView

urlpatterns = [
    path('quiz/', QuizView.as_view(), name='quiz'),
    path('auth/login/', LoginView.as_view(), name='login'),
]
