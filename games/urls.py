from django.urls import path
from . import views


urlpatterns = [
    path('games/', views.games, name='games'),
]