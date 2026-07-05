# Roadmapa Autonomicznej Automatyzacji AI (Z95)

## Kontekst

Przekuć obecne repo w kontrolowany system autonomicznej automatyzacji AI: boty jako interfejs, D1/SQLite jako pamięć operacyjna, execution packs jako zadania, review ledger jako bezpiecznik. Każdy krok ma gate bezpieczeństwa i rollback. Zasada nienaruszalna: **AI sugeruje, człowiek zatwierdza zmiany produkcyjne**.

Bazuje na `REKOMENDACJE_AUTONOMICZNEJ_AUTOMATYZACJI_AI_2026-05-14.md` (ścieżki 1-5) i rozwija o konkretne horyzonty oraz metryki.

## Przepływ danych

```
ingest -> staging -> AI suggestion -> human review -> export/release
```

Każdy etap jest event w D1, każdy ma status i rollback. Brak cichej ścieżki pomijającej review dla zmian produkcyjnych.

## Role agentów

| Rola | Zakres | Autonomia |
|------|--------|-----------|
| **importer** | Pull CERN/OLX/YouTube/etc. do staging (D1) | pełna (read-only upstream) |
| **verifier** | Walidacja schema, dedup, OCR | pełna (deterministyczna) |
| **curator** | AI suggestion: matching, normalizacja | sugestia (status `suggested`) |
| **reviewer** | Human review maintainera | zatwierdza/odrzuca (człowiek) |
| **exporter** | Eksport ecoEDA/CSV/exe pack | pełna, tylko dla `approved` |
| **operator** | Boty Discord/Telegram → queuing | inicjuje zadania autonomiczne bez ryzyka nadpisywania |

## Metryki minimalne

| Metryka | Cel | Bramka |
|---------|-----|--------|
| coverage danych | % encji z concheiden provenance | >80% przed eksportem |
| false-positive dopasowań | ratio odrzuconych / zatwierdzonych | <30% (powyżej = pauza curatora) |
| czas do review | P50 od `suggested` do `approved`/`rejected` | <72h |
| liczba zaakceptowanych / sprint | | rosnąca |
| rollback success rate | % rollbacków które nie poszcodziły danych | 100% (brak utraty) |

---

## Horyzont 1 — 2 tygodnie (fundament operacyjny)

Cel: zamknąć pętlę `ingest -> staging -> AI suggestion -> human review -> export` dla jednego obszaru (KiCad/CERN), z botem jako inicjatorem.

| Krok | Zakres | Gate | Rollback | Metryka |
|------|--------|------|----------|---------|
| A1 | Discord/Telegram wywołuje `!kicad` → kolejka pending | (gotowe z Z94) | brak zmian produkcyjnych | N wywołań/dobę |
| A2 | AI sugeruje dopasowanie KiCad -> NSIP (`suggested`) | AI nie może `approved` (Z90) | event `next_status=suggested` nie nadpisuje `recycled_part_master` | false-positive ratio |
| A3 | Maintener zatwierdza przez przycisk Discord (Z94) | `isMaintainer()` z env | odrzucenie zmnienia status na `rejected` + event | P50 czas do review |
| A4 | Eksport ecoEDA tylko dla `approved` (Z91) | brak `approved` = brak eksportu | regeneracja z D1, CSV to snapshot | N approved/sprint |

**Gate Horyzontu 1:** pętla KiCad działa end-to-end z co najmniej 5 approved linkami w ledgerze, bot inicuje bez nadpisywania `recycled_part_master`, eksport generuje diff przejrzany przez maintenera.

**Rollback H1:** Jeśli false-positive ratio >30% lub rollback success <100%: wstrzymać curatora, powrócić do manualnego dodawania sugestii, audit ostatnich 20 events.

---

## Horyzont 2 — 6 tygodni (rozszerzenie + metryki)

Cel: rozszerzyć na kolejne źródła (OLX, YouTube teardowny, datasheety), wprowadzić metryki jako health-check botów, kolejkowanie autonomicznych zadań.

| Krok | Zakres | Gate | Rollback | Metryka |
|------|--------|------|----------|---------|
| B1 | `importer` agent: harmonogramowany pull CERN/składniki staging | read-only; brak zapisu do `kicad_library_components` bez dedup | drop staging table, reingest | coverage |
| B2 | `verifier` agent: schema-diff + dedup + OCR deferred | deterministyczny; fail = status `needs_more_data` + event | re-verify z backupem | false-positive |
| B3 | `curator` agent: AI normalizacja (species/genus/mounting) | sugestia tylko; nie nadpisuje master | event `next_status=suggested` | coverage normalizacji |
| B4 | Metryki dashboard w D1: `automation_metrics` table | metryki są read-only dla agenta | drop metryki, regen z events | P50 czas do review |
| B5 | Bot inicjuje `execution_pack` (Project 13) jako autonomiczne zadanie bez nadpisywania katalogu | fork-first, PR-first, review-first (patrz CANARY_PILOT_PACKET) | zamknięcie PR bez merge | N PR/sprint |

**Gate Horyzontu 2:** wszystkie 5 metryk minimalnych mierzone automatycznie; bot może inicjować execution_pack bez ryzyka modyfikacji `recycled_part_master`; regresje KiCad posortowane w <72h.

**Rollback H2:** Jeśli metryki false-positive >30% przez 3 dni: curator przechodzi w tryb `suggest-only-audit` (sugeruje, ale wymaga potwierdzenia drugiego maintenera). Wstrzymać ingest nowych źródeł, audyt 50 ostatnich events.

---

## Horyzont 3 — 3 miesiące (autonomia z hardeningiem)

Cel: agent może samodzielnie utrzymać pipeline 24/7 bez ciągłej uwagi maintenera, ale w ciągu zdefiniowanych gate'ów. Węzły edge (smartfony/proot) włączone jako providery.

| Krok | Zakres | Gate | Rollback | Metryka |
|------|--------|------|----------|---------|
| C1 | Węzły edge (straz-edge-installer) rejestratory jako providery w D1 | write_token rotacja, `provider_id` konwencji | deaktywacja provider_id, nowe observation odrzucone | N providerów aktywnych |
| C2 | Agent `operator` bot zarządza kolejką zadań autonomicznych | każdy task ma `execution_pack` + reviewer wyznaczony | cancel task + closed status | N ukończonych/przerwanych |
| C3 | Auto-rollback na regresję: jeśli eksport psuje zgodność ecoEDA | checksum diff vs ostatni approved eksport | revert do poprzedniego snapshotu | rollback success rate |
| C4 | Self-healing ingest: retry z exponential backoff | maks. 3 retry/źródło, potem status `blocked` | mark `blocked` + alarm Discord | % `blocked`/dobę |
| C5 | Quarterly integrity review agenta (z `REVIEW_ROTATION_GOVERNANCE.md`) | jawny `IntegrityRiskAssessment` | zatrzymanie autonomii na review | pass/fall integrity |

**Gate Horyzontu 3:** pipeline działa 24/7 z <5% `blocked`/dobę; maintener interwiuje tylko dla approval producyjnych zmian; integrity review pokazauje brak `private_capture` / `opaque_approval_path`.

**Rollback H3:** Jeśli integrity review wykryje `private_capture`, `volunteer_work_appropriation` albo `opaque_approval_path`: zatrzymać autonomię, powrócić do H1 (manualny curator), audyt 90 dni events, jawne raport do społeczności.

---

## Bezpieczeństwo oraz węły krytyczne

- **AI nigdy nie może** zmienić `review_status` na `approved` bez maintenera (Z90, wymuszona w `kicad_review.js`).
- **Eksport nie rusza** `recycled_part_master` do produkcji do momentu `approved` i osobnej synchronizacji (Z91).
- **Boty są cienką warstwą** nad wspólną logiką (Z94): `discord_kicad_actions.js` → `kicad_review.js`.
- **Metryki są read-only** dla agentów: mierzone z `kicad_review_events`, nie nadpisywane.
- **Węzły edge** są providerami (P4 roadmapa edge) — nie mają bezpośredniego zapisu do katalogu; tylko do API Straży z `write_token`.

## Najlepiej zdefiniowana kolejka autonomicznych zadań (inicjowana przez bot)

Bot Discord/Telegram może inicjować bez ryzyka:
- `!kicad` — wylistuj pending (read-only).
- `!export ecoeda --format csv` — eksport approved (read-only snapshot).
- `!metrics` — pokaż health-check (read-only).
- `!scan-import cern --limit 50` — importer do staging (read-only upstream, write tylko staging).
- `!execution-pack start <id>` — uruchom pack z wymaganym reviewerem w CANARY mode.

Bot **NIE** może:
- Zatwierdzić `approved` bez maintenera.
- Nadpisać `recycled_part_master` bez z osobnej synchronizacji.
- Instalować pakietów / push bez PR / zmienić branch protection.
- Pominąć `IntegrityRiskAssessment` dla promotion do katalogu.

## Powiązania

- `docs/REKOMENDACJE_AUTONOMICZNEJ_AUTOMATYZACJI_AI_2026-05-14.md` — ścieżki bazowe.
- `docs/REVIEW_ROTATION_GOVERNANCE.md` — integrity review, rotacja reviewerów.
- `docs/MAPOWANIE_ENCJI_ORGANIZACJI_DO_D1_I_SQLITE.md` — encje w D1.
- `docs/ARCHITEKTURA_EDGE_SMARTFONY_CLOUD.md` — węzły edge jako providery (H3).
- `straz-edge-installer/` — installer dla węzłów edge (Tor B, dokończony).
- `cloudflare/src/kicad_review.js`, `discord_kicad_actions.js`, `ecoeda_export.js` — fundament H1.

## Status

DONE (2026-07-05). Roadmapa zgodna z Z95 kryteriami: 3 horyzonty (2tyg/6tyg/3mies), każdy krok ma gate + rollback + metrykę, zasada „AI sugeruje, człowiek zatwierdza zmiany produkcyjne" utrzymana we wszystkich horyzontach.
