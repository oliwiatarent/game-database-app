from django.urls import path
from . import views


urlpatterns = [
    path('games/', views.game_list, name='games'),
    path("game/<int:id>/", views.game, name="game"),
    path("add_game/", views.add_game, name="add_game"),
    path("add/<str:type>", views.add, name="add"),
    path("delete/<str:type>", views.delete, name="delete")
]