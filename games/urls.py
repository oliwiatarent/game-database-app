from django.urls import path
from . import views


urlpatterns = [
    path('games/', views.game_list, name='games'),
    path("game/<int:id>/", views.game, name="game"),
    path("game_form/", views.game_form, name="game_form")
]