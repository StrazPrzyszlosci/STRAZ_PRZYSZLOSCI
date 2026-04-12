# API: Inteligentna Akwakultura

Ten katalog zawiera minimalny, działający serwer HTTP dla pilotażu stawu hodowlanego.

## Dlaczego serwer jest potrzebny

Jeżeli Strażnicy Przyszłości mają naprawdę dostarczać dane do wspólnego systemu, to sam schemat i OpenAPI nie wystarczą. Potrzebny jest punkt wejścia, przez który provider może:

- zarejestrować się w systemie,
- przesłać obserwacje,
- przesłać zdarzenia,
- odebrać rekomendację,
- sprawdzić swój status.

## Obsługiwane endpointy

```text
POST /v1/providers/register
POST /v1/observations
POST /v1/events
POST /v1/recommendations/fish-pond
GET /v1/providers/{provider_id}/status
```

## Jak uruchomić

Z katalogu głównego repozytorium:

```bash
python3 api/server.py
```

Domyślnie serwer startuje na:

```text
http://127.0.0.1:8000
```

Możesz podać inny port:

```bash
python3 api/server.py 8080
```

## Minimalny przepływ

1. Provider rejestruje się przez `POST /v1/providers/register`.
2. Provider przesyła dane wody przez `POST /v1/observations`.
3. Provider może przesłać wynik lokalnej analizy zachowania ryb przez `POST /v1/events`.
4. Provider pobiera rekomendację przez `POST /v1/recommendations/fish-pond`.
5. Provider sprawdza stan integracji przez `GET /v1/providers/{provider_id}/status`.

## Założenia tej wersji

- serwer jest minimalny i działa bez zewnętrznych zależności,
- rejestr providerów oraz dane są trzymane w pamięci procesu,
- to nie jest jeszcze wersja produkcyjna,
- ta warstwa ma przede wszystkim umożliwić eksperymenty, integrację społeczności i rozwój wspólnego API.
