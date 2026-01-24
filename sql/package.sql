CREATE INDEX Index_Gry_Deweloper ON Gry(deweloper);
CREATE INDEX Index_Gry_Franczyza ON Gry(franczyza);
CREATE INDEX Index_Gry_Gra_Podstawowa ON Gry(gra_podstawowa);

CREATE INDEX Index_Gry_Tytul ON Gry(tytul);

CREATE INDEX Index_Gry_Gatunki_Gatunek ON Gry_Gatunki(nazwa_gatunku);

CREATE INDEX Index_Gry_Platformy_Platforma ON Gry_Platformy(nazwa_platformy);

CREATE INDEX Index_Wpisy_Uzytkownik ON Wpisy(ID_Uzytkownika);
CREATE INDEX Index_Wpisy_Gra ON Wpisy(ID_Gry);

CREATE INDEX Index_Recenzje_Uzytkownik ON Recenzje(ID_Uzytkownika);
CREATE INDEX Index_Recenzje_Gra ON Recenzje(ID_Gry);

CREATE INDEX Index_Listy_Uzytkownik ON Listy(ID_Uzytkownika);


CREATE OR REPLACE FUNCTION PoliczGryUzytkownika
    (pIdUzytkownika IN Uzytkownicy.ID%TYPE)
    RETURN INTEGER IS 
    vLiczbaGier INTEGER; 
BEGIN
    SELECT COUNT(*)
    INTO vLiczbaGier
    FROM Wpisy
    WHERE ID_Uzytkownika = pIdUzytkownika;

    RETURN vLiczbaGier;
END PoliczGryUzytkownika;


CREATE OR REPLACE FUNCTION PoliczSredniaOcen
    (pIdGry IN Gry.ID%TYPE)
    RETURN NUMBER IS 
    vSredniaOcen NUMBER(4, 2); 
BEGIN
    SELECT AVG(ocena)
    INTO vSredniaOcen
    FROM Recenzje
    WHERE ID_Gry = pIdGry;

    RETURN vSredniaOcen;
END PoliczSredniaOcen;


CREATE OR REPLACE PROCEDURE DodajZnajomego
    (pIdUzytkownika1 IN Uzytkownicy.ID%TYPE,
    pIdUzytkownika2 IN Uzytkownicy.ID%TYPE) IS
    vId1 INTEGER;
    vId2 INTEGER;
    vLiczbaWpisow INTEGER;
BEGIN
    IF pIdUzytkownika1 = pIdUzytkownika2 THEN
        RETURN;
    END IF;

    IF pIdUzytkownika1 < pIdUzytkownika2 THEN
        vId1 := pIdUzytkownika1;
        vId2 := pIdUzytkownika2;
    ELSE 
        vId1 := pIdUzytkownika2;
        vId2 := pIdUzytkownika1;
    END IF;

    SELECT COUNT(*)
    INTO vLiczbaWpisow
    FROM Znajomosci
    WHERE ID_Uzytkownik1 = vId1 AND ID_Uzytkownik2 = vId2;

    IF vLiczbaWpisow = 1 THEN
        RETURN;
    END IF;

    INSERT INTO Znajomosci VALUES (vId1, vId2);
END DodajZnajomego;


CREATE OR REPLACE PROCEDURE UsunZnajomego
    (pIdUzytkownika1 IN Uzytkownicy.ID%TYPE,
    pIdUzytkownika2 IN Uzytkownicy.ID%TYPE) IS
    vId1 INTEGER;
    vId2 INTEGER;
    vLiczbaWpisow INTEGER;
BEGIN
    IF pIdUzytkownika1 = pIdUzytkownika2 THEN
        RETURN;
    END IF;

    IF pIdUzytkownika1 < pIdUzytkownika2 THEN
        vId1 := pIdUzytkownika1;
        vId2 := pIdUzytkownika2;
    ELSE
        vId1 := pIdUzytkownika2;
        vId2 := pIdUzytkownika1;
    END IF;

    DELETE FROM Znajomosci
    WHERE ID_Uzytkownik1 = vId1 AND ID_Uzytkownik2 = vId2;
END UsunZnajomego;


CREATE TRIGGER PoAktualizacjiFranczyzy
    AFTER UPDATE ON Franczyzy
BEGIN
    UPDATE Gry
    SET franczyza = 'Brak'
    WHERE franczyza IS NULL;
END;


CREATE TRIGGER PoUsunieciuDewelopera
    AFTER DELETE ON Deweloperzy
BEGIN
    UPDATE Gry
    SET deweloper = (SELECT id FROM Deweloperzy WHERE nazwa = 'Brak')
    WHERE deweloper IS NULL;
END;
