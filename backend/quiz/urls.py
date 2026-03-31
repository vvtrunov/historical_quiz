from django.urls import path

from .views import QuizView

urlpatterns = [
    path('quiz/', QuizView.as_view(), name='quiz'),
]
