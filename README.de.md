# F1 Telemetry & Setup Toolkit

[English](README.md) | **Deutsch**

Ein Echtzeit-Telemetrie-Dashboard und ein datenbasierter Setup-Generator für F1 25/26 (Codemasters/EA Sports), aufgebaut auf dem UDP-Telemetrieprotokoll des Spiels.

## Funktionen

**Live-Telemetrie-Dashboard:** Liest den binären UDP-Datenstrom des Spiels in Echtzeit und stellt die Daten über WebSocket in einem Browser-Dashboard dar: eine Streckenkarte, die sich live aus den Positionsdaten aufbaut, Zeitabstände pro Kurvenabschnitt im Vergleich zur besten Runde der Session, Reifen- und Bremstemperaturen, ERS und die Rundenhistorie. Alles wird während der Fahrt in SQLite gespeichert.

**Rundenvergleich:** Lädt zwei beliebige aufgezeichnete Runden aus der Datenbank und legt Geschwindigkeit, Gas, Bremse, Gang und Drehzahl auf distanzbasierten Diagrammen übereinander. So sieht man genau, wo zwischen zwei Runden Zeit gewonnen oder verloren wird.

**Setup-Generator:** Eine eigenständige Web-App, die für jede Strecke im Kalender ein vollständiges Fahrzeug-Setup mit 18 Parametern ausgibt. Die Werte basieren auf recherchierten Community-Setups pro Strecke statt auf einer allgemeinen Formel (Quellen und Begründung in [`f1-26-meta-setups.md`](f1-26-meta-setups.md)).

## Aufbau

```
F1-Spiel  --UDP-Pakete-->  listener.py  --parst über packets.py-->  db.py (SQLite)
                                |
                                +--WebSocket-->  dashboard.html (Live-Ansicht)
                                +--HTTP-API--->  compare.html (Rundenanalyse)
```

- `listener.py`: UDP-Listener, WebSocket-Server und kleiner HTTP-Server in einem Prozess
- `packets.py`: Parser für die binären F1-Telemetriepakete (Motion, Lap Data, Car Telemetry, Session, Events usw.)
- `db.py`: SQLite-Speicherung von Sessions, Runden und Telemetrie pro Frame
- `dashboard.html`: Live-Dashboard im Browser (JavaScript ohne Framework, Streckenkarte per Canvas)
- `compare.html`: Diagramme für den Rundenvergleich
- `f1-26-setup-guide.html`: der Setup-Generator (unabhängig vom Telemetrie-Teil, läuft komplett im Browser)

## Technik

Python (asyncio, `websockets`) im Backend, SQLite als Datenbank, HTML/CSS/JavaScript ohne Framework im Frontend. Kein Build-Schritt, alles läuft lokal.

## Schnellstart

```
1. Im Spiel unter Einstellungen die UDP-Telemetrie aktivieren (Port 20777, Format passend zur Spielversion)
2. start.bat doppelklicken (installiert die eine Abhängigkeit und startet alles)
3. Während der Fahrt http://localhost:8766/dashboard öffnen
```

Ausführliche Anleitung mit Port-Übersicht und Fehlerbehebung (auf Englisch): [`SETUP.md`](SETUP.md).

## Warum es dieses Projekt gibt

Ich wollte beim Fahren mit einem neuen Lenkrad eine konkrete Frage beantworten: In welcher Kurve verliere ich genau Zeit, und liegt es am Setup oder an mir? Die Zeitabstände pro Kurvenabschnitt und der Rundenvergleich machen das sichtbar, statt es zu raten. Der Setup-Generator ist aus der Recherche entstanden, wie sich Setups im Spiel tatsächlich verhalten. Das folgt nämlich nicht immer der echten Fahrzeugphysik.
