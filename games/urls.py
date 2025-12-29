from django.urls import path
from . import views


urlpatterns = [
    path('games/', views.game_list, name='game_list'),
    path("game/<int:id>/", views.game, name="game")
]