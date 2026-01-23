import oracledb
from dotenv import dotenv_values

config = dotenv_values(".env")
username = config.get("USERNAME")
password = config.get("PASSWD")
cs = config.get("CS")

try:
    with oracledb.connect(user=username, password=password, dsn=cs) as connection:
        with connection.cursor() as cursor:

            print("\n--- TABELA: UZYTKOWNICY ---")
            cursor.execute("SELECT ID, NAZWA, EMAIL, HASLO FROM Uzytkownicy")
            users = cursor.fetchall()
            if not users:
                print("brak.")
            for row in users:
                print(f"ID: {row[0]} | Nazwa: {row[1]} | Email: {row[2]}")

            print("\n--- TABELA: LISTY ---")
            cursor.execute("SELECT ID, NAZWA, ID_UZYTKOWNIKA FROM Listy")
            lists = cursor.fetchall()
            for row in lists:
                print(f"Lista ID: {row[0]} | Nazwa: {row[1]} | Właściciel ID: {row[2]}")

            print("\n--- TABELA: DEWELOPERZY ---")
            cursor.execute("SELECT ID, NAZWA FROM Deweloperzy")
            rows = cursor.fetchall()
            if not rows: print("brak.")
            for row in rows:
                print(f"ID: {row[0]} | Nazwa: {row[1]}")

            print("\n--- TABELA: GRY ---")
            cursor.execute("SELECT ID, TYTUL, DATA_WYDANIA FROM Gry")
            rows = cursor.fetchall()
            if not rows: print("brak.")
            for row in rows:
                print(f"ID: {row[0]} | Tytuł: {row[1]} | Data: {row[2]}")

            print("\n--- TABELA: RECENZJE ---")
            cursor.execute("SELECT ID, ID_UZYTKOWNIKA, ID_GRY, OCENA, KOMENTARZ FROM Recenzje")
            rows = cursor.fetchall()
            if not rows: print("brak.")
            for row in rows:
                print(f"ID: {row[0]} | User ID: {row[1]} | Gra ID: {row[2]} | Ocena: {row[3]} | Komentarz: {row[4]}")

            print("\n--- TABELA: WPISY ---")
            cursor.execute("SELECT ID_UZYTKOWNIKA, ID_GRY, CZAS, CZY_UKONCZONA, CZY_ULUBIONA FROM Wpisy")
            rows = cursor.fetchall()
            if not rows: print("brak.")
            for row in rows:
                print(f"User ID: {row[0]} | Gra ID: {row[1]} | Czas: {row[2]}h | Ukończona: {row[3]} | Ulubiona: {row[4]}")

            print("\n--- TABELA: GRY_W_LISCIE ---")
            cursor.execute("SELECT ID_LISTY, ID_GRY FROM Gry_w_liscie")
            rows = cursor.fetchall()
            if not rows: print("brak.")
            for row in rows:
                print(f"Lista ID: {row[0]} | Gra ID: {row[1]}")

            print("\n--- TABELA: GATUNKI ---")
            cursor.execute("SELECT NAZWA FROM Gatunki")
            rows = cursor.fetchall()
            if not rows: print("brak.")
            for row in rows:
                print(f"{row[0]}")

            print("\n--- TABELA: PLATFORMY ---")
            cursor.execute("SELECT NAZWA FROM Platformy")
            rows = cursor.fetchall()
            for row in rows:
                print(f"{row[0]}")

            print("\n--- TABELA: FRANCZYZY ---")
            cursor.execute("SELECT NAZWA FROM Franczyzy")
            rows = cursor.fetchall()
            if not rows: print("brak.")
            for row in rows:
                print(f"{row[0]}")

            print("\n--- TABELA: GRY_GATUNKI ---")
            cursor.execute("SELECT ID_GRY, NAZWA_GATUNKU FROM Gry_Gatunki")
            rows = cursor.fetchall()
            if not rows: print("brak.")
            for row in rows:
                print(f"Gra ID: {row[0]} Gatunek: {row[1]}")

            print("\n--- TABELA: GRY_PLATFORMY ---")
            cursor.execute("SELECT ID_GRY, NAZWA_PLATFORMY FROM Gry_Platformy")
            rows = cursor.fetchall()
            if not rows: print("brak.")
            for row in rows:
                print(f"Gra ID: {row[0]} Platforma: {row[1]}")

except Exception as e:
    print(f"{e}")