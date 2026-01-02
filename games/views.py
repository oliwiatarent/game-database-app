from django.shortcuts import render, redirect
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
            cursor.execute(f"SELECT id, tytul, okladka FROM {username}.gry ORDER BY tytul")

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


            # Przetwarzanie gry podstawowej dla dodatków
            if game["dodatek"] == 1:
                cursor.execute(f"""
                    SELECT tytul 
                    FROM Gry
                    WHERE ID = {game["gra_podstawowa"]}
                """)

                for item in cursor:
                    game["tytul_gry_podstawowej"] = item[0]


    return render(request, "game.html", {
        "game": game
    })


def game_form(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        releaseDate = request.POST.get('releaseDate')
        ageRating = request.POST.get('ageRating')
        boxart = request.POST.get('boxart')
        description = request.POST.get('description')
        developer = request.POST.get('developer')
        franchise = request.POST.get('franchise')
        dlc = request.POST.get('dlc')
        dlcBaseGame = request.POST.get('dlcBaseGame')
        genres = request.POST.getlist('genres')
        platforms = request.POST.getlist('platforms')

        print(platforms)

        with oracledb.connect(user=username, password=password, dsn=cs) as connection:
            with connection.cursor() as cursor:
                if dlc == 'on':
                    dlc = 1
                    cursor.execute('SELECT id FROM Gry WHERE tytul = :1', (dlcBaseGame, ))

                    for item in cursor:
                        dlcBaseGame = item[0]
                else:
                    dlc = 0
                    dlcBaseGame = None

                query = '''INSERT INTO Gry VALUES (
                    null,
                    :1,
                    TO_DATE(:2, 'YYYY-MM-DD'),
                    :3,
                    :4,
                    :5,
                    (SELECT id FROM Deweloperzy WHERE nazwa = :6),
                    :7,
                    :8,
                    :9)
                '''

                cursor.execute(query, (title, releaseDate, int(ageRating), boxart, description, developer, franchise, dlc, dlcBaseGame))

                connection.commit()

                for platform in platforms:
                    query = '''
                        INSERT INTO Gry_Platformy VALUES (
                            (SELECT id FROM gry WHERE tytul = :1),
                            :2
                        )
                    '''
                    cursor.execute(query, (title, platform))

                for genre in genres:
                    query = '''
                        INSERT INTO Gry_Gatunki VALUES (
                            (SELECT id FROM gry WHERE tytul = :1),
                            :2
                        )
                    '''
                    cursor.execute(query, (title, genre))

                connection.commit()

        return redirect('games')

    developers = []
    franchises = []
    baseGames = []
    platforms = []
    genres = []

    with oracledb.connect(user=username, password=password, dsn=cs) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT nazwa FROM deweloperzy")

            for item in cursor:
                developers.append({
                    "nazwa": item[0]
                })

            cursor.execute("SELECT nazwa FROM franczyzy")

            for item in cursor:
                franchises.append({
                    "nazwa": item[0]
                })

            cursor.execute("SELECT tytul FROM gry WHERE dodatek = 0")

            for item in cursor:
                baseGames.append({
                    "tytul": item[0]
                })

            cursor.execute("SELECT nazwa FROM platformy")

            for item in cursor:
                platforms.append({
                    "nazwa": item[0]
                })

            cursor.execute("SELECT nazwa FROM gatunki")

            for item in cursor:
                genres.append({
                    "nazwa": item[0]
                })


    return render(request, "game_form.html", {
        "developers": developers,
        "franchises": franchises,
        "baseGames": baseGames,
        "platforms": platforms,
        "genres": genres
    })