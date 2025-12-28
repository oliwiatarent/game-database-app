from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from dotenv import dotenv_values
import oracledb


def games(request):
    config = dotenv_values(".env")
    username = config["USERNAME"]
    password = config["PASSWD"]
    cs = config["CS"]

    games_list = []

    with oracledb.connect(user=username, password=password, dsn=cs) as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT id, tytul, okladka FROM {username}.gry")

            for id, tytul, okladka in cursor:
                 games_list.append({
                    "id": id,
                    "title": tytul,
                    "boxart": okladka
                 })

    return render(request, "game_list.html", {
        "games": games_list
    })