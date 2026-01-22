from django.urls import path
from . import views


urlpatterns = [
    path('', views.game_list, name='games'),
    path('games/', views.game_list, name='games'),
    path("game/", views.game, name="game"),
    path("game_form/<str:action>", views.game_form, name="game_form"),
    path("add/<str:type>", views.add, name="add"),
    path("delete/<str:type>", views.delete, name="delete"),
    path("delete_game/<int:id>", views.delete_game, name="delete_game"),
    path('login/', views.login_user, name='login'),
    path('register/', views.register_user, name='register'),
    path('logout/', views.logout_user, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('search_game/', views.search_game, name='search_game'),
    path('add_entry/<int:game_id>/', views.add_entry, name='add_entry'),
    path('search_review/', views.search_review, name='search_review'),
    path('add_review/<int:game_id>/', views.add_review, name='add_review')
]