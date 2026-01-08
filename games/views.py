from django.shortcuts import render, redirect
from dotenv import dotenv_values
import oracledb

config = dotenv_values(".env")
username = config["USERNAME"]
password = config["PASSWD"]
cs = config["CS"]


def game_list(request):

    games_list = []

    try:
        with oracledb.connect(user=username, password=password, dsn=cs) as connection:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT id, tytul, okladka FROM {username}.gry ORDER BY tytul")

                for id, tytul, okladka in cursor:
                     games_list.append({
                        "id": id,
                        "title": tytul,
                        "boxart": okladka
                     })
    except:
        return render(request, 'error.html')


    return render(request, "game_list.html", {
        "games": games_list
    })


def game(request):

    id = request.GET.get("id")

    game = {}
    columns = []
    genres_list = []
    platform_list = []

    try:
        with oracledb.connect(user=username, password=password, dsn=cs) as connection:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name 
                    FROM user_tab_columns 
                    WHERE table_name = 'GRY'
                """)
    
                for column in cursor:
                    columns.append(column[0].lower())
    
                sql = f"SELECT * FROM {username}.gry WHERE id = :1"
                cursor.execute(sql, (id, ))
    
                game_row = cursor.fetchone()
                for i in range(len(game_row)):
    
                    if columns[i] == "ograniczenie_wiekowe":
                        attribute = 'img/age_ratings/' + str(game_row[i]) + '.png'
                    elif columns[i] == "data_wydania":
                        attribute = game_row[i].date
                    else:
                        attribute = game_row[i]
    
                    game[columns[i]] = attribute
    
    
                # Przetwarzanie dewelopera
                sql = f"""
                    SELECT nazwa 
                    FROM {username}.gry g INNER JOIN deweloperzy d ON d.id = g.deweloper
                    WHERE g.id = :1
                """
                cursor.execute(sql, (id,))
    
                game["deweloper"] = cursor.fetchone()[0]
    
                # Przetwarzanie gatunków
                sql = f"""
                    SELECT nazwa_gatunku 
                    FROM Gry_Gatunki
                    WHERE ID_Gry = :1
                """
                cursor.execute(sql, (id, ))
    
                for item in cursor:
                    genres_list.append(item[0])
    
                if len(genres_list) == 0:
                    game["gatunki"] = "Brak"
                else:
                    game["gatunki"] = ', '.join(genres_list)
    
    
                # Przetwarzanie platform
                sql = f"""
                    SELECT nazwa_platformy
                    FROM Gry_Platformy
                    WHERE ID_Gry = :1
                """
                cursor.execute(sql, (id, ))
    
                for item in cursor:
                    platform_list.append(item[0])
    
                if len(platform_list) == 0:
                    game["platformy"] = "Brak"
                else:
                    game["platformy"] = ', '.join(platform_list)
    
    
                # Przetwarzanie gry podstawowej dla dodatków
                if game["dodatek"] == 1:
                    sql = f"""
                        SELECT tytul 
                        FROM Gry
                        WHERE ID = :1
                    """
                    cursor.execute(sql, (game["gra_podstawowa"], ))
    
                    game["tytul_gry_podstawowej"] = cursor.fetchone()[0]

    except TypeError as ex:
        return render(request, 'error.html', {
            "information": "Gra o podanym id nie istnieje w bazie danych"
        })
    except:
        return render(request, 'error.html')

    return render(request, "game.html", {
        "game": game
    })


def game_form(request, action):
    if request.method == 'POST':
        id = request.GET.get('id')
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

        try:
            with oracledb.connect(user=username, password=password, dsn=cs) as connection:
                with connection.cursor() as cursor:
                    if dlc == 'on':
                        dlc = 1
                        cursor.execute('SELECT id FROM Gry WHERE tytul = :1', (dlcBaseGame, ))

                        dlcBaseGame = cursor.fetchone()[0]
                    else:
                        dlc = 0
                        dlcBaseGame = None

                    if action == 'add':
                        query = '''
                            INSERT INTO Gry VALUES (null, :1, TO_DATE(:2, 'YYYY-MM-DD'), :3, :4, :5,
                            (SELECT id FROM Deweloperzy WHERE nazwa = :6), :7, :8, :9)
                        '''
                        cursor.execute(query, (title, releaseDate, int(ageRating), boxart, description, developer, franchise, dlc, dlcBaseGame))
                    else:
                        query = '''
                            UPDATE Gry SET tytul = :1, data_wydania = TO_DATE(:2, 'YYYY-MM-DD'), ograniczenie_wiekowe = :3,
                            okladka = :4, opis = :5, deweloper = (SELECT id FROM Deweloperzy WHERE nazwa = :6), franczyza = :7,
                            dodatek = :8, gra_podstawowa = :9
                            WHERE id = :10
                        '''
                        cursor.execute(query, (title, releaseDate, int(ageRating), boxart, description, developer, franchise, dlc, dlcBaseGame, id))

                        query = '''
                            DELETE FROM Gry_Platformy
                            WHERE ID_Gry = :1
                        '''
                        cursor.execute(query, (id, ))

                        query = '''
                            DELETE FROM Gry_Gatunki
                            WHERE ID_Gry = :1
                        '''
                        cursor.execute(query, (id, ))


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
        except:
            return render(request, 'error.html')

        return redirect('games')


    values = ["title", "releaseDate", "ageRating", "boxart", "developer", "franchise", "description", "dlc", "dlcBaseGame"]
    default_values = {}
    developers = []
    franchises = []
    baseGames = []
    platforms = []
    default_platforms = []
    default_genres = []
    genres = []

    try:
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

                if action == "edit":
                    id = request.GET.get("id")
                    query = """SELECT tytul, data_wydania, ograniczenie_wiekowe, okladka, deweloper, 
                        franczyza, opis, dodatek, gra_podstawowa FROM Gry WHERE id = :1"""
                    cursor.execute(query, (id, ))

                    result = cursor.fetchone()
                    for i in range(len(values)):
                        if result[i] is not None:
                            if values[i] == "releaseDate":
                                default_values[values[i]] = result[i].strftime("%Y-%m-%d")
                            else:
                                default_values[values[i]] = result[i]

                    query = "SELECT nazwa FROM Deweloperzy WHERE id = :1"
                    cursor.execute(query, (int(default_values["developer"]), ))
                    default_values["developer"] = cursor.fetchone()[0]

                    if "dlcBaseGame" in default_values and default_values["dlcBaseGame"] is not None:
                        query = "SELECT tytul FROM Gry WHERE id = :1"
                        cursor.execute(query, (int(default_values["dlcBaseGame"]),))
                        default_values["dlcBaseGame"] = cursor.fetchone()[0]

                    query = '''
                        SELECT nazwa_platformy FROM Gry_Platformy
                        WHERE ID_Gry = :1
                    '''
                    cursor.execute(query, (id, ))

                    for item in cursor:
                        default_platforms.append(item[0])

                    if len(default_platforms) > 0:
                        default_values["platforms"] = default_platforms

                    query = '''
                        SELECT nazwa_gatunku FROM Gry_Gatunki
                        WHERE ID_Gry = :1
                    '''
                    cursor.execute(query, (id,))

                    for item in cursor:
                        default_genres.append(item[0])

                    if len(default_genres) > 0:
                        default_values["genres"] = default_genres
    except:
        return render(request, 'error.html')


    if action == 'edit':
        edit = 1
    else:
        edit = 0

    return render(request, "game_form.html", {
        "developers": developers,
        "franchises": franchises,
        "baseGames": baseGames,
        "platforms": platforms,
        "genres": genres,
        "default_values": default_values,
        "edit": edit
    })


def add(request, type):

    if request.method == 'POST':
        value = request.POST.get('value')

        try:
            with oracledb.connect(user=username, password=password, dsn=cs) as connection:
                with connection.cursor() as cursor:

                    if type == 'gatunek':
                        sql = "INSERT INTO Gatunki VALUES (:1)"
                    if type == 'platforma':
                        sql = "INSERT INTO Platformy VALUES (:1)"
                    if type == 'franczyza':
                        sql = "INSERT INTO Franczyzy VALUES (:1)"
                    if type == 'deweloper':
                        sql = "INSERT INTO Deweloperzy VALUES (null, :1)"

                    cursor.execute(sql, (value, ))
                    connection.commit()
        except:
            return render(request, 'error.html')

        return redirect('games')

    return render(request, "add_form.html", {
        "type": type
    })


def delete(request, type):

    if request.method == 'POST':
        attribute = request.POST.get('attribute')

        try:
            with oracledb.connect(user=username, password=password, dsn=cs) as connection:
                with connection.cursor() as cursor:

                    if type == 'gatunek':
                        sql = "DELETE FROM Gatunki WHERE nazwa = :1"
                    if type == 'platforma':
                        sql = "DELETE FROM Platformy WHERE nazwa = :1"
                    if type == 'franczyza':
                        sql = "DELETE FROM Franczyzy WHERE nazwa = :1"
                    if type == 'deweloper':
                        sql = "DELETE FROM Deweloperzy WHERE nazwa = :1"

                    cursor.execute(sql, (attribute, ))
                    connection.commit()
        except:
            return render(request, 'error.html')

        return redirect('games')


    attributes = []

    try:
        with oracledb.connect(user=username, password=password, dsn=cs) as connection:
            with connection.cursor() as cursor:
                if type == 'gatunek':
                    sql = "SELECT nazwa FROM Gatunki"
                if type == 'platforma':
                    sql = "SELECT nazwa FROM Platformy"
                if type == 'franczyza':
                    sql = "SELECT nazwa FROM Franczyzy WHERE nazwa NOT LIKE 'Brak'"
                if type == 'deweloper':
                    sql = "SELECT nazwa FROM Deweloperzy WHERE nazwa NOT LIKE 'Brak'"
                if type == 'gra':
                    sql = "SELECT tytul FROM Gry"

                cursor.execute(sql)

                for item in cursor:
                    attributes.append(item[0])
    except:
        return render(request, 'error.html')


    return render(request, "delete_form.html", {
        "type": type,
        "attributes": attributes
    })


def delete_game(request, id):

    try:
        with oracledb.connect(user=username, password=password, dsn=cs) as connection:
            with connection.cursor() as cursor:
                sql = """
                    DELETE FROM Gry
                    WHERE id = :1
                """

                cursor.execute(sql, (id, ))

                connection.commit()
    except:
        return render(request, 'error.html')

    return redirect("games")

