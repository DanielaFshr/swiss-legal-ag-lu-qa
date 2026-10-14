# Projektübersicht

Dieses Repo enthält nur den für die Abgabe relevanten Stand. Frühere Pakete und Pilotnotebooks bleiben ausserhalb des Repos archiviert.

## Reproduktion

`make run` am Repo-Stamm baut das Docker-Image und berechnet die Endergebnisse aus gespeicherten Antworten und Urteilen. `make run-local` berechnet dieselben Ergebnisse mit lokalem Python. Der Ablauf prüft 300 eindeutige Antworten, die Eingabedateien, 126 correct und 174 incorrect sowie die ursprüngliche Judge–Mensch-Übereinstimmung von 42/57.

## Neue Modellantworten

Für einen neuen Modelllauf verwendet `src/inference.py` die Variablen LLM_NAME, LLM_BASE_URL und LLM_API_KEY. Standardmodell ist swiss-ai/Apertus-v1.5-70B:featherless-ai am Hugging-Face-Router. Der Token wird nicht gespeichert. Temperatur 0 und max_tokens 1200. Der optionale neue Lauf benötigt API-Guthaben und wird nicht automatisch gestartet. Gespeicherte Antworten werden beim Fortsetzen übersprungen. Neue Antworten erfordern neue Judge-Urteile und erhalten keine alten Labels.

Die reproduzierbare Hauptauswertung benötigt diese API-Funktion nicht. Ein erneuter Inferenzlauf kann bei einem gehosteten Modell trotz gleicher Einstellungen abweichende Texte liefern. Die originalen technischen Protokolle liegen im separaten Abschlussarchiv. Bei ins_003 wurde nach einer abgeschnittenen Antwort ein zusätzlicher Versuch mit 2400 Tokens verwendet.

## Evidenz

docs/evidence enthält die exakten Bewertungsgrundlagen, Antworten, originalen Judge-Urteile und gesonderten Abschlussentscheidungen. Die Unterlagen unter audit erhalten die ursprüngliche menschliche Stichprobe und den alten agr_003-Fall. So ist die neue Frage klar von der ursprünglichen Stichprobe getrennt.

26 Fälle wurden gemeinsam besprochen. agr_003 wurde danach präzisiert, erneut beantwortet und abschliessend anhand des neuen Judge-Urteils geprüft. In der finalen Antwortsammlung bestehen 59 unveränderte menschliche Stichprobenlabels. Die ursprüngliche unabhängige Prüfung umfasste 60 Antworten. Diese Zahlen dürfen nicht vermischt werden.

## Öffentliche Reviewbelege

Die öffentlichen Dateien enthalten ausformulierte Bewertungsbegründungen und unveränderte ursprüngliche Labels. Wörtliche Chatbestätigungen und Gesprächszeitpunkte sind nicht enthalten. Die Originale verbleiben im separaten Arbeitsarchiv.
