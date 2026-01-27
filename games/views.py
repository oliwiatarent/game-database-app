import shutil

from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password, check_password
from dotenv import dotenv_values
import oracledb
import os

from game_database_app import settings

config = dotenv_values(".env")
username = config["USERNAME"]
password = config["PASSWD"]
cs = config["CS"]


def process_file(boxart):
    upload_folder = os.path.join(settings.MEDIA_ROOT, 'boxart')
    static_folder = os.path.join(settings.BASE_DIR, 'static', 'img', 'boxart')
    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(static_folder, exist_ok=True)
    filename = boxart.name
    file_path = os.path.join(upload_folder, filename)
    destination = os.path.join(static_folder, filename)

    with open(file_path, 'wb+') as f:
        for chunk in boxart.chunks():
            f.write(chunk)

    shutil.copy(file_path, destination)

    if os.path.exists(file_path):
        os.remove(file_path)

    return 'img/boxart/' + filename


def process_avatar(avatar):
    upload_folder = os.path.join(settings.MEDIA_ROOT, 'avatars')
    static_folder = os.path.join(settings.BASE_DIR, 'static', 'img', 'avatars')
    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(static_folder, exist_ok=True)
    filename = avatar.name
    file_path = os.path.join(upload_folder, filename)
    destination = os.path.join(static_folder, filename)

    with open(file_path, 'wb+') as f:
        for chunk in avatar.chunks():
            f.write(chunk)

    shutil.copy(file_path, destination)

    if os.path.exists(file_path):
        os.remove(file_path)

    return 'img/avatars/' + filename


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
    reviews_list = []

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

                # Przetwarzanie oceny
                avg_rating = cursor.callfunc('PoliczSredniaOcen', oracledb.NUMBER, [id])

                if avg_rating is not None:
                    game['average_rating'] = round(avg_rating, 1)
                else:
                    game['average_rating'] = "N/A"

                # Przetwarzanie recenzji
                sql = """
                        SELECT r.ocena, r.komentarz, r.data_wystawienia, u.nazwa, u.zdjecie_profilowe, u.ID
                        FROM Recenzje r
                        JOIN Uzytkownicy u ON r.ID_Uzytkownika = u.ID
                        WHERE r.ID_Gry = :1
                        ORDER BY r.data_wystawienia DESC
                """
                cursor.execute(sql, (id,))

                for row in cursor:
                    reviews_list.append({
                        "rating": row[0],
                        "comment": row[1],
                        "date": row[2],
                        "username": row[3],
                        "user_avatar": row[4],
                        "user_id": row[5]
                    })

    except TypeError as ex:
        return render(request, 'error.html', {
            "information": "Gra o podanym id nie istnieje w bazie danych"
        })
    except:
        return render(request, 'error.html')

    return render(request, "game.html", {
        "game": game,
        "reviews": reviews_list
    })


def game_form(request, action):
    if request.method == 'POST':
        id = request.GET.get('id')
        title = request.POST.get('title')
        releaseDate = request.POST.get('releaseDate')
        ageRating = request.POST.get('ageRating')
        boxart = request.FILES.get('boxart')
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

                    if boxart:
                        boxart_path = process_file(boxart)

                    if action == 'add':
                        if boxart is None:
                            boxart_path = 'img/boxart/default.png'

                        query = '''
                            INSERT INTO Gry VALUES (null, :1, TO_DATE(:2, 'YYYY-MM-DD'), :3, :4, :5,
                            (SELECT id FROM Deweloperzy WHERE nazwa = :6), :7, :8, :9)
                        '''
                        cursor.execute(query, (title, releaseDate, int(ageRating), boxart_path, description, developer, franchise, dlc, dlcBaseGame))
                    else:
                        if boxart is None:
                            query = '''
                                UPDATE Gry SET tytul = :1, data_wydania = TO_DATE(:2, 'YYYY-MM-DD'), ograniczenie_wiekowe = :3,
                                opis = :4, deweloper = (SELECT id FROM Deweloperzy WHERE nazwa = :5), franczyza = :6,
                                dodatek = :7, gra_podstawowa = :8
                                WHERE id = :9
                            '''
                            cursor.execute(query, (title, releaseDate, int(ageRating), description, developer, franchise, dlc, dlcBaseGame, id))
                        else:
                            query = '''
                                UPDATE Gry SET tytul = :1, data_wydania = TO_DATE(:2, 'YYYY-MM-DD'), ograniczenie_wiekowe = :3,
                                okladka = :4, opis = :5, deweloper = (SELECT id FROM Deweloperzy WHERE nazwa = :6), franczyza = :7,
                                dodatek = :8, gra_podstawowa = :9
                                WHERE id = :10
                            '''
                            cursor.execute(query, (title, releaseDate, int(ageRating), boxart_path, description, developer, franchise, dlc, dlcBaseGame, id))

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
                cursor.execute("SELECT nazwa FROM deweloperzy ORDER BY nazwa")

                for item in cursor:
                    developers.append({
                        "nazwa": item[0]
                    })

                cursor.execute("SELECT nazwa FROM franczyzy ORDER BY nazwa")

                for item in cursor:
                    franchises.append({
                        "nazwa": item[0]
                    })

                cursor.execute("SELECT tytul FROM gry WHERE dodatek = 0 ORDER BY tytul")

                for item in cursor:
                    baseGames.append({
                        "tytul": item[0]
                    })

                cursor.execute("SELECT nazwa FROM platformy ORDER BY nazwa")

                for item in cursor:
                    platforms.append({
                        "nazwa": item[0]
                    })

                cursor.execute("SELECT nazwa FROM gatunki ORDER BY nazwa")

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


def register_user(request):
    if request.method == 'POST':
        nazwa = request.POST.get('username')
        email = request.POST.get('email')
        haslo = request.POST.get('password')
        powtorz_haslo = request.POST.get('confirm_password')

        if haslo != powtorz_haslo:
            return render(request, 'register.html', {
                'error': 'Podane hasła nie są identyczne!'
            })
        haslo_hash = make_password(haslo)

        try:
            with oracledb.connect(user=username, password=password, dsn=cs) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT count(*) FROM Uzytkownicy WHERE nazwa = :1 OR email = :2", (nazwa, email))
                    if cursor.fetchone()[0] > 0:
                        return render(request, 'register.html',
                                      {'error': 'Użytkownik o takiej nazwie lub emailu już istnieje!'})

                    query = """
                        INSERT INTO Uzytkownicy (nazwa, email, haslo, administrator)
                        VALUES (:1, :2, :3, 0)
                    """
                    cursor.execute(query, (nazwa, email, haslo_hash))
                    connection.commit()

            return redirect('login')

        except Exception as e:
            return render(request, 'register.html', {'error': f'Błąd rejestracji: {e}'})

    return render(request, 'register.html')


def login_user(request):
    if request.method == 'POST':
        nazwa = request.POST.get('username')
        haslo = request.POST.get('password')

        try:
            with oracledb.connect(user=username, password=password, dsn=cs) as connection:
                with connection.cursor() as cursor:
                    query = "SELECT ID, haslo, administrator, zdjecie_profilowe FROM Uzytkownicy WHERE nazwa = :1"
                    cursor.execute(query, (nazwa,))
                    user_row = cursor.fetchone()

                    if user_row:
                        db_id, db_password, db_is_admin, db_avatar = user_row

                        if check_password(haslo, db_password):
                            request.session['user_id'] = db_id
                            request.session['user_name'] = nazwa
                            request.session['is_admin'] = db_is_admin
                            request.session['user_avatar'] = db_avatar

                            return redirect('games')
                        else:
                            return render(request, 'login.html', {'error': 'Nieprawidłowe hasło!'})
                    else:
                        return render(request, 'login.html', {'error': 'Nie ma takiego użytkownika!'})
        except Exception as e:
            return render(request, 'login.html', {'error': f'Błąd: {e}'})

    return render(request, 'login.html')


def logout_user(request):
    request.session.flush()
    return redirect('games')


def profile(request, user_id=None):
    viewer_id = request.session.get('user_id')
    if user_id:
        target_id = user_id
    else:
        if viewer_id:
            target_id = viewer_id
        else:
            return redirect('login')
    # tu żeby zawsze był zainicjalizowany
    is_owner = (viewer_id == target_id)
    is_friend = False

    if viewer_id and not is_owner:
        try:
            with oracledb.connect(user=username, password=password, dsn=cs) as connection:
                with connection.cursor() as cursor:
                    # słownik bo kursor chciał 4 zmienne
                    sql = """
                        SELECT count(*) FROM Znajomosci 
                        WHERE (ID_Uzytkownik1 = :u1 AND ID_Uzytkownik2 = :u2) 
                           OR (ID_Uzytkownik1 = :u2 AND ID_Uzytkownik2 = :u1)
                    """
                    cursor.execute(sql, {'u1': viewer_id, 'u2': target_id})
                    if cursor.fetchone()[0] > 0:
                        is_friend = True
        except Exception as e:
            print(f"{e}")

    user_data = {}
    user_games = []
    user_reviews = []
    user_lists = []
    user_friends = []

    try:
        with oracledb.connect(user=username, password=password, dsn=cs) as connection:
            with connection.cursor() as cursor:
                query_user = """
                    SELECT nazwa, email, zdjecie_profilowe, opis, data_zalozenia 
                    FROM Uzytkownicy 
                    WHERE ID = :1
                """
                cursor.execute(query_user, (target_id,))
                result = cursor.fetchone()

                if result:
                    user_data = {
                        "id": target_id,  # do znajomości
                        "nazwa": result[0],
                        "email": result[1],
                        "avatar": result[2],
                        "opis": result[3],
                        "data_zalozenia": result[4]
                    }
                game_count = cursor.callfunc('PoliczGryUzytkownika', oracledb.NUMBER, [target_id])
                user_data['game_count'] = int(game_count) if game_count else 0

                query_games = """
                    SELECT g.id, g.tytul, g.okladka, w.czy_ulubiona
                    FROM Gry g
                    JOIN Wpisy w ON g.id = w.ID_Gry
                    WHERE w.ID_Uzytkownika = :1
                    ORDER BY g.tytul
                """
                cursor.execute(query_games, (target_id,))

                for row in cursor:
                    user_games.append({
                        "id": row[0],
                        "title": row[1],
                        "boxart": row[2],
                        "is_fav": row[3]
                    })

                query_reviews = """
                    SELECT r.ocena, r.komentarz, r.data_wystawienia, g.tytul, g.okladka, g.id
                    FROM Recenzje r
                    JOIN Gry g ON r.ID_Gry = g.ID
                    WHERE r.ID_Uzytkownika = :1
                    ORDER BY r.data_wystawienia DESC
                    FETCH FIRST 3 ROWS ONLY
                                """
                cursor.execute(query_reviews, (target_id,))

                for row in cursor:
                    user_reviews.append({
                        "rating": row[0],
                        "comment": row[1],
                        "date": row[2],
                        "game_title": row[3],
                        "game_boxart": row[4],
                        "game_id": row[5]
                    })

                query_lists = """
                    SELECT l.id, l.nazwa, l.opis, l.data_utworzenia,
                           (SELECT COUNT(*) FROM Gry_w_liscie gl WHERE gl.ID_Listy = l.ID) as liczba_gier
                    FROM Listy l
                    WHERE l.ID_Uzytkownika = :1
                    ORDER BY l.data_utworzenia DESC
                """
                cursor.execute(query_lists, (target_id,))

                raw_lists = cursor.fetchall()

                for row in raw_lists:
                    list_id = row[0]
                    list_obj = {
                        "id": list_id,
                        "name": row[1],
                        "desc": row[2],
                        "date": row[3],
                        "count": row[4],
                        "previews": []  # na okładki
                    }

                    query_previews = """
                        SELECT g.okladka 
                        FROM Gry g
                        JOIN Gry_w_liscie gl ON g.ID = gl.ID_Gry
                        WHERE gl.ID_Listy = :1
                        ORDER BY gl.data_dodania DESC
                        FETCH FIRST 5 ROWS ONLY
                    """
                    cursor.execute(query_previews, (list_id,))

                    for row in cursor:
                        list_obj["previews"].append(row[0])

                    user_lists.append(list_obj)

                    query_friends = """
                        SELECT u.id, u.nazwa, u.zdjecie_profilowe
                        FROM Uzytkownicy u
                        WHERE u.ID IN (
                            SELECT ID_Uzytkownik2 FROM Znajomosci WHERE ID_Uzytkownik1 = :1
                            UNION
                            SELECT ID_Uzytkownik1 FROM Znajomosci WHERE ID_Uzytkownik2 = :2
                        )
                    """
                    # z union target 2 razy
                    cursor.execute(query_friends, (target_id, target_id))

                    for row in cursor:
                        user_friends.append({
                            "id": row[0],
                            "name": row[1],
                            "avatar": row[2]
                        })
    except Exception as e:
        print(f"{e}")
        return render(request, 'error.html')

    return render(request, 'profile.html', {
        'user': user_data,
        'games': user_games,
        'reviews': user_reviews,
        'lists': user_lists,
        'friends': user_friends,
        'is_owner': is_owner,
        'is_friend': is_friend
    })


def search_game(request):
    query = request.GET.get('q')
    results = []

    if query:
        try:
            with oracledb.connect(user=username, password=password, dsn=cs) as connection:
                with connection.cursor() as cursor:
                    sql = """
                        SELECT id, tytul, okladka, data_wydania 
                        FROM Gry 
                        WHERE LOWER(tytul) LIKE LOWER(:1)
                        ORDER BY tytul
                    """
                    cursor.execute(sql, (f"%{query}%",))

                    for row in cursor:
                        results.append({
                            "id": row[0],
                            "title": row[1],
                            "boxart": row[2],
                            "date": row[3]
                        })
        except Exception:
            return render(request, 'error.html')

    return render(request, 'search_game.html', {'results': results, 'query': query})


def add_entry(request, game_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    if request.method == 'POST':
        w_trakcie = 1 if request.POST.get('w_trakcie') == 'on' else 0
        czy_ukonczona = 1 if request.POST.get('czy_ukonczona') == 'on' else 0
        sto_procent = 1 if request.POST.get('sto_procent') == 'on' else 0
        czy_ulubiona = 1 if request.POST.get('czy_ulubiona') == 'on' else 0
        czas_r = request.POST.get('czas')
        czas = 0.0
        if czas_r:
            try:
                czas = float(czas_r.replace(',', '.'))
            except ValueError:
                czas = 0.0

        try:
            with oracledb.connect(user=username, password=password, dsn=cs) as connection:
                with connection.cursor() as cursor:
                    check_sql = "SELECT count(*) FROM Wpisy WHERE ID_Uzytkownika = :1 AND ID_Gry = :2"
                    cursor.execute(check_sql, (user_id, game_id))

                    # wpis już istnieje
                    if cursor.fetchone()[0] > 0:
                        sql = """
                            UPDATE Wpisy SET 
                            w_trakcie = :1, czy_ukonczona = :2, sto_procent = :3, czy_ulubiona = :4, czas = :5
                            WHERE ID_Uzytkownika = :6 AND ID_Gry = :7
                        """
                        cursor.execute(sql, (w_trakcie, czy_ukonczona, sto_procent, czy_ulubiona, czas, user_id, game_id))
                    else:
                        sql = """
                            INSERT INTO Wpisy (ID_Uzytkownika, ID_Gry, w_trakcie, czy_ukonczona, sto_procent, czy_ulubiona, czas)
                            VALUES (:1, :2, :3, :4, :5, :6, :7)
                        """
                        cursor.execute(sql, (user_id, game_id, w_trakcie, czy_ukonczona, sto_procent, czy_ulubiona, czas))

                    connection.commit()
            return redirect('profile')

        except Exception as e:
            #print(f"{e}")
            return render(request, 'error.html')

    # do nagłówka
    game_info = {}
    try:
        with oracledb.connect(user=username, password=password, dsn=cs) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT tytul, okladka FROM Gry WHERE id = :1", (game_id,))
                row = cursor.fetchone()
                if row:
                    game_info = {"title": row[0], "boxart": row[1]}
    except:
        pass

    return render(request, 'entry_form.html', {'game': game_info})


def edit_profile(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    current_desc = ""
    current_avatar = ""
    current_password_hash = ""

    try:
        with oracledb.connect(user=username, password=password, dsn=cs) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT opis, zdjecie_profilowe, haslo FROM Uzytkownicy WHERE ID = :1", (user_id,))
                row = cursor.fetchone()
                if row:
                    current_desc = row[0]
                    current_avatar = row[1]
                    current_password_hash = row[2]
    except Exception as e:
        print(f"Błąd pobierania profilu!: {e}")
        return render(request, 'error.html')

    if request.method == 'POST':
        new_desc = request.POST.get('description')
        new_avatar_file = request.FILES.get('avatar')
        new_password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if new_avatar_file:
            final_avatar = process_avatar(new_avatar_file)
        else:
            final_avatar = current_avatar

        if new_password:
            if new_password != confirm_password:
                return render(request, 'edit_profile.html', {
                    'error': 'Nowe hasła nie są identyczne!',
                    'description': current_desc
                })
            final_password = make_password(new_password)
        else:
            final_password = current_password_hash

        if new_desc is None:
            new_desc = current_desc

        try:
            with oracledb.connect(user=username, password=password, dsn=cs) as connection:
                with connection.cursor() as cursor:
                    sql = """
                        UPDATE Uzytkownicy 
                        SET opis = :1, zdjecie_profilowe = :2, haslo = :3
                        WHERE ID = :4
                    """
                    cursor.execute(sql, (new_desc, final_avatar, final_password, user_id))
                    connection.commit()

            request.session['user_avatar'] = final_avatar
            return redirect('profile')

        except Exception as e:
            print(f"{e}")
            return render(request, 'edit_profile.html', {'error': 'Błąd zapisu do bazy danych!'})

    return render(request, 'edit_profile.html', {'description': current_desc})


def search_review(request):
    query = request.GET.get('q')
    results = []

    if query:
        try:
            with oracledb.connect(user=username, password=password, dsn=cs) as connection:
                with connection.cursor() as cursor:
                    sql = """
                        SELECT id, tytul, okladka, data_wydania 
                        FROM Gry 
                        WHERE LOWER(tytul) LIKE LOWER(:1)
                        ORDER BY tytul
                    """
                    cursor.execute(sql, (f"%{query}%",))

                    for row in cursor:
                        results.append({
                            "id": row[0],
                            "title": row[1],
                            "boxart": row[2],
                            "date": row[3]
                        })
        except Exception as e:
            return render(request, 'error.html')

    return render(request, 'search_review.html', {'results': results, 'query': query})


def add_review(request, game_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    if request.method == 'POST':
        ocena = request.POST.get('rating')
        komentarz = request.POST.get('comment')

        try:
            with oracledb.connect(user=username, password=password, dsn=cs) as connection:
                with connection.cursor() as cursor:
                    check_sql = "SELECT id FROM Recenzje WHERE ID_Uzytkownika = :1 AND ID_Gry = :2"
                    cursor.execute(check_sql, (user_id, game_id))
                    existing_review = cursor.fetchone()

                    # update dla istniejącej recenzji
                    if existing_review:
                        review_id = existing_review[0]
                        sql = """
                            UPDATE Recenzje 
                            SET ocena = :1, komentarz = :2, data_wystawienia = CURRENT_TIMESTAMP
                            WHERE id = :3
                        """
                        cursor.execute(sql, (ocena, komentarz, review_id))
                    else:
                        sql = """
                            INSERT INTO Recenzje (ocena, komentarz, ID_Uzytkownika, ID_Gry)
                            VALUES (:1, :2, :3, :4)
                        """
                        cursor.execute(sql, (ocena, komentarz, user_id, game_id))

                    connection.commit()

            return redirect('games')

        except Exception as e:
            return render(request, 'error.html')

    game_info = {}
    existing_data = {'rating': '', 'comment': ''}

    try:
        with oracledb.connect(user=username, password=password, dsn=cs) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT tytul, okladka FROM Gry WHERE id = :1", (game_id,))
                row = cursor.fetchone()
                if row:
                    game_info = {"title": row[0], "boxart": row[1]}

                cursor.execute("SELECT ocena, komentarz FROM Recenzje WHERE ID_Uzytkownika = :1 AND ID_Gry = :2",
                               (user_id, game_id))
                review_row = cursor.fetchone()
                if review_row:
                    existing_data = {'rating': review_row[0], 'comment': review_row[1]}

    except Exception:
        return render(request, 'error.html')

    return render(request, 'review_form.html', {'game': game_info, 'review': existing_data})


def create_list(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    if request.method == 'POST':
        nazwa = request.POST.get('name')
        opis = request.POST.get('description')

        try:
            with oracledb.connect(user=username, password=password, dsn=cs) as connection:
                with connection.cursor() as cursor:
                    # RETURNING ID INTO do szybkiego pobrania ID nowej listy
                    id_var = cursor.var(int)
                    sql = """
                        INSERT INTO Listy (nazwa, opis, ID_Uzytkownika)
                        VALUES (:1, :2, :3)
                        RETURNING ID INTO :4
                    """
                    cursor.execute(sql, (nazwa, opis, user_id, id_var))
                    new_list_id = id_var.getvalue()[0]
                    connection.commit()

            return redirect('list_details', list_id=new_list_id)
        except Exception as e:
            print(f"{e}")
            return render(request, 'error.html')

    return render(request, 'list_form.html')


def list_details(request, list_id):
    user_id = request.session.get('user_id')

    list_data = {}
    list_games = []
    search_results = []
    query = request.GET.get('q')

    try:
        with oracledb.connect(user=username, password=password, dsn=cs) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT nazwa, opis, ID_Uzytkownika FROM Listy WHERE ID = :1", (list_id,))
                row = cursor.fetchone()
                if not row:
                    return render(request, 'error.html')

                list_data = {"id": list_id, "name": row[0], "desc": row[1], "owner_id": row[2]}

                sql = """
                    SELECT g.id, g.tytul, g.okladka, gl.data_dodania
                    FROM Gry g
                    JOIN Gry_w_liscie gl ON g.ID = gl.ID_Gry
                    WHERE gl.ID_Listy = :1
                    ORDER BY gl.data_dodania DESC
                """
                cursor.execute(sql, (list_id,))
                for r in cursor:
                    list_games.append({"id": r[0], "title": r[1], "boxart": r[2], "added_date": r[3]})

                if user_id == list_data['owner_id'] and query:
                    sql_search = """
                        SELECT id, tytul, okladka FROM Gry 
                        WHERE LOWER(tytul) LIKE LOWER(:1) 
                        AND id NOT IN (SELECT ID_Gry FROM Gry_w_liscie WHERE ID_Listy = :2)
                        FETCH FIRST 5 ROWS ONLY
                    """
                    cursor.execute(sql_search, (f"%{query}%", list_id))
                    for r in cursor:
                        search_results.append({"id": r[0], "title": r[1], "boxart": r[2]})

    except Exception as e:
        print(f"{e}")
        return render(request, 'error.html')

    return render(request, 'list_details.html', {
        'list': list_data,
        'games': list_games,
        'search_results': search_results,
        'query': query,
        'is_owner': (user_id == list_data['owner_id'])
    })


def add_game_to_list(request, list_id, game_id):
    user_id = request.session.get('user_id')
    try:
        with oracledb.connect(user=username, password=password, dsn=cs) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT ID_Uzytkownika FROM Listy WHERE ID = :1", (list_id,))
                row = cursor.fetchone()
                if row and row[0] == user_id:
                    cursor.execute("INSERT INTO Gry_w_liscie (ID_Gry, ID_Listy) VALUES (:1, :2)", (game_id, list_id))
                    connection.commit()
    except Exception as e:
        print(f"{e}")
        pass
    return redirect('list_details', list_id=list_id)


def remove_game_from_list(request, list_id, game_id):
    user_id = request.session.get('user_id')
    try:
        with oracledb.connect(user=username, password=password, dsn=cs) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT ID_Uzytkownika FROM Listy WHERE ID = :1", (list_id,))
                row = cursor.fetchone()
                if row and row[0] == user_id:
                    cursor.execute("DELETE FROM Gry_w_liscie WHERE ID_Gry = :1 AND ID_Listy = :2", (game_id, list_id))
                    connection.commit()
    except Exception as e:
        print(f"{e}")
        pass
    return redirect('list_details', list_id=list_id)


def global_search(request):
    query = request.GET.get('q')
    found_games = []
    found_users = []

    if query:
        try:
            with oracledb.connect(user=username, password=password, dsn=cs) as connection:
                with connection.cursor() as cursor:
                    sql_games = """
                        SELECT id, tytul, okladka, data_wydania 
                        FROM Gry 
                        WHERE LOWER(tytul) LIKE LOWER(:1)
                        ORDER BY tytul
                        FETCH FIRST 10 ROWS ONLY
                    """
                    cursor.execute(sql_games, (f"%{query}%",))
                    for row in cursor:
                        found_games.append({
                            "id": row[0],
                            "title": row[1],
                            "boxart": row[2],
                            "date": row[3]
                        })

                    sql_users = """
                        SELECT id, nazwa, zdjecie_profilowe 
                        FROM Uzytkownicy 
                        WHERE LOWER(nazwa) LIKE LOWER(:1)
                        ORDER BY nazwa
                        FETCH FIRST 10 ROWS ONLY
                    """
                    cursor.execute(sql_users, (f"%{query}%",))
                    for row in cursor:
                        found_users.append({
                            "id": row[0],
                            "name": row[1],
                            "avatar": row[2]
                        })

        except Exception as e:
            print(f"{e}")
            return render(request, 'error.html')

    return render(request, 'global_search.html', {
        'games': found_games,
        'users': found_users,
        'query': query
    })


def add_friend(request, friend_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    try:
        with oracledb.connect(user=username, password=password, dsn=cs) as connection:
            with connection.cursor() as cursor:
                cursor.callproc('DodajZnajomego', [user_id, friend_id])
                connection.commit()
    except Exception as e:
        print(f"{e}")
        return render(request, 'error.html')

    return redirect('profile_view', user_id=friend_id)


def remove_friend(request, friend_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    try:
        with oracledb.connect(user=username, password=password, dsn=cs) as connection:
            with connection.cursor() as cursor:
                cursor.callproc('UsunZnajomego', [user_id, friend_id])
                connection.commit()
    except Exception as e:
        print(f"{e}")
        return render(request, 'error.html')

    return redirect('profile_view', user_id=friend_id)