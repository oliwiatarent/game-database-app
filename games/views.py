from django.shortcuts import render
from dotenv import dotenv_values
import oracledb

config = dotenv_values(".env")
username = config["USERNAME"]
password = config["PASSWD"]
cs = config["CS"]


def game_list(request):

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


def game(request, id):

    game = {}
    columns = []

    with oracledb.connect(user=username, password=password, dsn=cs) as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name 
                FROM user_tab_columns 
                WHERE table_name = 'GRY'
            """)

            for column in cursor:
                columns.append(column[0].lower())

            cursor.execute(f"SELECT * FROM {username}.gry WHERE id = {id}")

            for item in cursor:
                for i in range(len(item)):
                    game[columns[i]] = item[i]

            print(game)


    return render(request, "game.html", {
        "game": game
    })