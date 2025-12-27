from django.shortcuts import render
from django.http import HttpResponse
from dotenv import dotenv_values
import oracledb


def games(request):
    config = dotenv_values(".env")
    username = config["USERNAME"]
    password = config["PASSWD"]
    cs = config["CS"]

    with oracledb.connect(user=username, password=password, dsn=cs) as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {username}.gry")

            html = "<h1>Lista gier</h1><ul>"
            for item in cursor:
                html += f"<li>{item}</li>"
            html += "</ul>"

    return HttpResponse(html)