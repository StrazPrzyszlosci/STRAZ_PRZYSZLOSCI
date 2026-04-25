# Mini-Handoff Zadanie 19

## Gdzie dodano instrukcje setupu sekretow

- `PROJEKTY/13_baza_czesci_recykling/README.md` — nowa sekcja "Jak ustawic sekrety (klucze API i tokeny)" z krok po kroku instrukcja pozyskania `GITHUB_PAT`, `YOUTUBE_API_KEY`, `GEMINI_API_KEY` i przeniesienia do Kaggle Secrets
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-enrichment-01/RUNBOOK.md` — rozbudowana sekcja "Wymagane sekrety" z szczegolami pozyskania kluczy, instrukcja `.env` i Kaggle Secrets krok po kroku
- `docs/WOLONTARIUSZE_GOTOWE_PRZYDZIALY.md` — zaktualizowane referencje do README sekcja "Jak ustawic sekrety" i `.env.example`; dodane linki do VOLUNTEER_TERMS_OF_PARTICIPATION i VOLUNTEER_FALLBACK_GUIDE

## Zmienne w `.env.example`

- `GITHUB_PAT` — Fine-grained token z Contents: Read and write do forka
- `YOUTUBE_API_KEY` — API key z Google Cloud Console po wlaczeniu YouTube Data API v3
- `GEMINI_API_KEY` — API key z Google AI Studio

Kazda zmienna ma opis krokow pozyskania, URL-e do konsol i uwagi o limitach quota.

## Ktore pozycje readiness to domknelo

- Sekcja 1.2 Sekrety w `PUBLIC_VOLUNTEER_RUN_READINESS.md`: status zmieniony z **DO POTWIERDZENIA** na **GOTOWE**
- Linia "Sekrety sa prawidlowo ustawione w Kaggle Secrets" w sekcji DO POTWIERDZENIA: uzupelniona o informacje, ze instrukcja jest dostepna
- Dodano wpis "Instrukcja setupu sekretow dla wolontariusza" w sekcji DOMKNIETE W TEJ ITERACJI

## Co nadal zostaje do potwierdzenia

- **Weryfikacja scope `GITHUB_PAT` w notebooku** — notebook nie sprawdza, czy token ma wystarczajace uprawnienia; wolontariusz moze ustawic zly scope i push nie zadziala. Do decyzji operatora: czy dodac pre-flight check scope.
- **Pre-flight check quota YouTube i Gemini** — notebook nie sprawdza wyczerpania quota przed startem. Do decyzji operatora: czy dodac sprawdzenie.
- **Realne wykonanie setupu przez wolontariusza** — instrukcja jest gotowa, ale nie byla jeszcze przetestowana przez osobe spoza projektu (test uzytecznosci runbooka pozostaje NIE GOTOWE).
- **Branch protection na upstream** — nadal DO POTWIERDZENIA (poza zakresem zadania 19).
- **Obsadzenie rotacji review** — nadal CZESCIOWO (poza zakresem zadania 19).
