from django.urls import path
from . import views


urlpatterns = [
    path('games/', views.game_list, name='games'),
    path("game/", views.game, name="game"),
    path("game_form/<str:action>", views.game_form, name="game_form"),
    path("add/<str:type>", views.add, name="add"),
    path("delete/<str:type>", views.delete, name="delete")
]