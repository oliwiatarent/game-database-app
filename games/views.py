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

                    if columns[i] == "ograniczenie_wiekowe":
                        attribute = 'img/age_ratings/' + str(item[i]) + '.png'
                    else:
                        attribute = item[i]

                    game[columns[i]] = attribute

            cursor.execute(f"""
                SELECT nazwa 
                FROM {username}.gry g INNER JOIN deweloperzy d ON d.id = g.deweloper
                WHERE g.id = {id}
            """)

            for item in cursor:
                game["deweloper"] = item[0]


    return render(request, "game.html", {
        "game": game
    })