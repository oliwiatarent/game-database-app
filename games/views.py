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
                    elif columns[i] == "data_wydania":
                        attribute = item[i].date
                    else:
                        attribute = item[i]

                    game[columns[i]] = attribute


            # Przetwarzanie dewelopera
            cursor.execute(f"""
                SELECT nazwa 
                FROM {username}.gry g INNER JOIN deweloperzy d ON d.id = g.deweloper
                WHERE g.id = {id}
            """)

            for item in cursor:
                game["deweloper"] = item[0]


            # Przetwarzanie gatunków
            cursor.execute(f"""
                SELECT nazwa_gatunku 
                FROM Gry_Gatunki
                WHERE ID_Gry = {id}
            """)

            genres_list = []
            for item in cursor:
                genres_list.append(item[0])

            if len(genres_list) == 0:
                game["gatunki"] = "None"
            else:
                game["gatunki"] = ', '.join(genres_list)


            # Przetwarzanie platform
            cursor.execute(f"""
                SELECT nazwa_platformy 
                FROM Gry_Platformy
                WHERE ID_Gry = {id}
            """)

            platform_list = []
            for item in cursor:
                platform_list.append(item[0])

            if len(platform_list) == 0:
                game["platformy"] = "None"
            else:
                game["platformy"] = ', '.join(platform_list)


    return render(request, "game.html", {
        "game": game
    })