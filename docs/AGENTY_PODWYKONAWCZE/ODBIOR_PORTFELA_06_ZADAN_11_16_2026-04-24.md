# Odbior Portfela 06 Zadan 11-16 2026-04-24

## Cel dokumentu

Ten dokument zapisuje odbior zlecen `11-16` z portfela:

- `docs/AGENTY_PODWYKONAWCZE/PORTFEL_06_ZLECEN_DLA_PODWYKONAWCOW_2026-04-23.md`

Wazne: ten odbior dotyczy **obecnego lokalnego worktree**, a nie potwierdza jeszcze, ze wszystkie te wyniki sa juz w kanonicznym, zcommitowanym stanie repo.

## Komendy walidacyjne wykonane przy odbiorze

- `python3 -m py_compile PROJEKTY/13_baza_czesci_recykling/scripts/verify_candidates.py`
- `python3 PROJEKTY/13_baza_czesci_recykling/scripts/verify_candidates.py dry-run`
- parsowanie `manifest.json` dla:
  - `pack-project13-kaggle-verification-01`
  - `pack-project13-blueprint-design-01`
  - `pack-project13-esp-runtime-01`
- `git diff --check`

## Werdykt zbiorczy

- `11`: `PASS z uwaga`
- `12`: `PASS z uwaga`
- `13`: `PASS z uwaga`
- `14`: `PASS`
- `15`: `PASS`
- `16`: `PASS z uwaga`

Nie ma zadan z werdyktem `FAIL`, ale kilka z nich zostawia istotne otwarte luki operacyjne.

## Odbior per zadanie

### `11` Verification real execution surface

- Werdykt: `PASS z uwaga`
- Co uznaje za dowiezione:
  - istnieje realny execution surface `PROJEKTY/13_baza_czesci_recykling/scripts/verify_candidates.py`
  - pack verification ma status `smoke_tested`
  - output contract jest jawny w `manifest.json`
  - suchy przebieg przechodzi lokalnie i zostawia review-ready artefakty `.dry-run`
- Co pozostaje otwarte:
  - OCR check dla `disputed` nadal wymaga `GEMINI_API_KEY`
  - obecny surface jest lokalnym CLI, nie osobnym notebookiem Kaggle
  - 30 rekordow pozostaje `disputed`, wiec verification nie jest jeszcze praktycznie domkniety

### `12` Public volunteer pilot packet

- Werdykt: `PASS z uwaga`
- Co uznaje za dowiezione:
  - istnieje fallback guide
  - istnieja terms of participation
  - istnieje issue template do zglaszania problemow
  - readiness realnie zamyka czesc dawnych pozycji `NIE GOTOWE`
- Co pozostaje otwarte:
  - kanal na zywo nadal jest `do_potwierdzenia`
  - readiness w sekcji sekretow nadal ma status `DO POTWIERDZENIA`
  - nadal brakuje publicznej instrukcji skad wziasc `GITHUB_PAT`, `YOUTUBE_API_KEY`, `GEMINI_API_KEY` oraz jak ustawic je krok po kroku

### `13` Pilot review assignment and approval

- Werdykt: `PASS z uwaga`
- Co uznaje za dowiezione:
  - istnieje operacyjny scaffold review/approval
  - sa pola `__DO_UZUPELNIENIA__` dla rol review/approval
  - approval path i exception flow sa czytelne
- Co pozostaje otwarte:
  - brak realnie wpisanych osob i loginow
  - readiness nie moze przejsc z `CZESCIOWO` na `GOTOWE`, dopoki maintainer nie wypelni scaffolda

### `14` Blueprint design brief template

- Werdykt: `PASS`
- Co uznaje za dowiezione:
  - istnieje szablon design brief
  - istnieje sample brief
  - szablon rozroznia reuse parts, missing parts i zalozenia
- Co pozostaje otwarte:
  - brak formalnego walidatora albo schema contract
  - gestosc `parts_master.jsonl` jest nadal zbyt mala dla realnego BOM

### `15` ESP32 recovered board profile template

- Werdykt: `PASS`
- Co uznaje za dowiezione:
  - istnieje template board profile
  - istnieje sample profile
  - pola `[POMIERZONE]`, `[DOMNIEMANE]`, `[BRAKUJACE]` sa rozdzielone jawnie
- Co pozostaje otwarte:
  - brak bench test contract
  - brak polityki `simulated vs real hardware`

### `16` Blueprint and ESP runtime pack skeletons

- Werdykt: `PASS z uwaga`
- Co uznaje za dowiezione:
  - oba katalogi packow istnieja
  - oba maja komplet dokumentacyjnego skeletonu
  - `CHAIN_MAP.md` zostal zaktualizowany
  - `esp-runtime-01` ma ostrzejszy governance variant `B`
- Co pozostaje otwarte:
  - brak execution surface dla obu packow
  - brak bench test contract dla `esp-runtime-01`
  - oba packi sa nadal poprawnie tylko `draft`, nie gotowe do uruchomienia

## Najwazniejsze otwarte luki po odbiorze

1. Verification ma surface, ale nadal nie ma domknietego review packetu dla 30 `disputed`.
2. Curation nie zostala jeszcze przetestowana na prawdziwym `test_db_verified.jsonl` jako stabilnym downstream input.
3. Wolontariusz nadal nie dostaje pelnej instrukcji pozyskania kluczy i ustawienia `.env` / `Kaggle Secrets`.
4. Pilot review scaffold istnieje, ale nie ma realnie wpisanych rol ani potwierdzonego branch protection.
5. `blueprint-design-01` i `esp-runtime-01` maja skeletony, ale nadal brakuje im kontraktow walidacyjnych przed pierwszym surface.

## Wniosek portfelowy

Portfel `06` mozna uznac za **odebrany warunkowo**:

- fundamenty dla `verification`, `public volunteer pilot`, `Blueprint` i `ESP runtime` istnieja,
- ale kolejny portfel musi uderzyc w realne domkniecie luk wykonawczych i onboardingowych, a nie w kolejne szkielety dokumentacyjne.
