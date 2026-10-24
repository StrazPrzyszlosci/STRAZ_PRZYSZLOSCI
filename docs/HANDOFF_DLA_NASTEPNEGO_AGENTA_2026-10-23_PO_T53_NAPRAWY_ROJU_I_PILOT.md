# Handoff po T53 — naprawy rdzenia roju i ograniczony pilot

Data: 2026-10-23. Baza: main `6859480`. Branch/worktree: `codex/T53-T55-swarm-recommendations` / `.kilo/worktrees/codex-swarm-recommendations`.

## Zakres i własność

Po wskazaniu dwóch nakładających się claimów T53 operator polecił „zatrzymałem kilo.. rób ty”. Przejęcie zapisano we własnym claimie. Cudzych claimów, worktree, konfiguracji Kilo i WIP nie edytowano. Następnie przygotowano dokładny plan i zweryfikowano starszy audyt. Operator wznowił pracę poleceniem „poprawiaj i uruchamiaj rój” oraz jawnie dopuścił klucz lokalnego OmniRoute przy braku zmiennej. Klucza nie zapisano ani nie wypisano.

Tura obejmuje pięć obszarów: koordynację/CI, wykonanie, budżet, granice workera, pilot i metryki. Pełny plan 31 zmian ma nadal otwarte etapy. Nazwa brancha nie rezerwuje osobno T54/T55 z wcześniejszych handoffów. Main, konfiguracja gatewaya i ochrona gałęzi pozostają bez zmian.

## Co zmieniono

- Łańcuch przekazuje wyniki wcześniejszych etapów. Brak zależności i stop blokują dalsze wywołania; błędy dają failed/degraded. Nieudane joby pozostają do ponowienia. Przed nowym jobem wymagane są minimum cztery próby budżetu. Fallback ma limit dwóch prób i respektuje kandydatów routera.
- Jeden atomowy ledger przechowuje zużycie i okno RPM, resetuje dobę bez restartu i konserwatywnie dzieli pule providerów. Rezerwacja poprzedza wywołanie. Quota gate obejmuje OmniRoute/evolve-only; strategy, review oraz proxy Hermesa korzystają z tego samego ledgeru.
- Privacy pochodzi z wejścia; brak lokalnego engine daje odmowę. Feedback nie jest jobem procdev. Typy decyzji są rozdzielone, etykiety walidowane/deduplikowane, fit batch idempotentny i używany też w ewolucji.
- Free-only używa jawnych modeli oraz dopuszczonych identyfikatorów odpowiedzi. Provider ani katalog nie rozszerza sam allowlisty. Latencja API jest mierzona. Wykrycie biblioteki nie udaje użycia jej algorytmu.
- Ewolucja przeplata źródła, utrwala fingerprinty, omija aktywne zadania i używa wstrzykniętego workera. Review dostaje pliki z kwarantanny. Mock ma status simulated; gotowość wymaga wykonania, skanu, walidacji i review.
- Bubblewrap odcina hostową sieć i HOME; jedyny kanał API to rozliczany Unix proxy. Klucz gatewaya nie trafia do Hermesa. Brak odrębnego runtime blokuje rzeczywistego workera. Produkcja pozostaje w kwarantannie.
- Nowe narzędzie claims rezerwuje atomowo pod wspólną blokadą Git. Zakresy plików sprawdza dla nowych claimów z metadanymi; starsze tylko po numerze. Pełna suita ma nowy workflow PR. Administracyjne ustawienie required check pozostaje otwarte.

## Weryfikacja — liczby obowiązkowe

```text
python3 -m unittest discover -s tests -p 'test_*.py'   494 OK
node --test tests/*.mjs                               378 pass / 0 fail
node --check cloudflare/src/*.js (pętla per plik)       OK
node --check tools/run_swarm_pilot.mjs                 OK
python3 agentic_cells/validate_cell_manifest.py        12 manifestów OK
python3 human_approval/validate_record.py              2 rekordy ważne
python3 human_approval/expiry_report.py                0 expired / 0 expiring_soon
python3 tools/agent_claims.py check --all-worktrees     brak konfliktów po przejęciu
git diff --check                                     OK
```

Regresje sprawdzają kontekst draft/review, zależności, privacy bez sieci, retryability, 8 prób=8, konkurujące rezerwacje, rollover/RPM, dedup i odrzucenie pustych/symlinkowych artefaktów. Rzeczywiste lokalne próby sandboxa potwierdziły brak dostępu do wskazanego pliku HOME i /etc/shadow. Przebieg sandbox → relay → Unix proxy → atrapowy upstream wykonał dokładnie jedno żądanie i zapisał jedną próbę. To test mechanizmu, nie pełnego zainstalowanego Hermesa.

## Piloty i dowody

- Offline: 2 cykle, 2 zadania ukończone, 8/8 prób mock poprawnych; ewolucja tworzy jawne symulacje.
- Realnie: publiczne przykłady resource_scout; konkretne modele `kilocode/cohere/north-mini-code:free` i `kilocode/nvidia/nemotron-3.5-lightning:free`.
- Pierwszy limit 8 ukończył jedno zadanie. Próby z timeoutem 25 s ujawniły zbyt krótki limit; przebieg przy łącznym limicie 12 zachował prawdziwy status degraded. Nie zerowano ledgeru.
- Po analizie czasów 6–24 s timeout zwiększono do 60 s, a łączny limit jawnie do 16. Ostatni run: **4 etapy, 4 udane próby, status ok**; kolejny cykl: no_new_jobs.
- Łącznie: **16 prób, 10 udanych wywołań, 6 timeoutów, 2 ukończone zadania**. Historyczne failed/degraded pozostają w receiptach. Trace, ledger i stan są zgodne.
- Przeczytano fragmenty draftów i review: recenzja odnosi się do draftu i brakującej ewidencji. Wyniki są do oceny człowieka; przykłady nie są zweryfikowanymi ofertami sprzętu ani aktywacją.
- Human acceptance: **0 etykiet**. Nie ma dowodu poprawy uczenia. Limity operatora nie są pomiarem limitów upstream; zapisano `upstream_quota_verified=false`.

Artefakty: `scratch/selfopt/pilot-{offline,live}/`; logi kontroli: `scratch/selfopt/verification/`. Liczby i hashe receiptów: `docs/ROJ_PILOT_T53_2026-10-23.json`. Ostatni source_manifest zgadza się z bieżącym kodem Python. Pilot zakończył się po limitach; nie działa bezterminowo w tle. Instrukcje: `docs/RUNBOOK_PILOTA_ROJU_T53_2026-10-23.md`.

## Otwarte etapy — najwyżej pięć kolejnych prac

1. Odebrać PR rdzenia, ocenić artefakty i nadać prawdziwe etykiety decyzjom. Powodzenie API nie jest akceptacją merytoryczną.
2. Przygotować runtime Hermesa bez sekretów; przeprowadzić odrębny ograniczony pilot produkcji patcha i testów. Nie montować całego prywatnego HOME.
3. Dodać rzeczywistą publikację draft PR przez rój po gotowości artefaktu. Obecna kolejka nie publikuje PR; no_auto_merge/no_direct_push pozostają obowiązkowe.
4. Domknąć retry/backoff i lifecycle indeksu ewolucji po przerwaniu; zweryfikować rzeczywiste pule oraz reset upstream i required check w ochronie main.
5. Na podstawie etykiet i baseline ocenić kalibrację oraz kandydatów MAP-Elites/GEPA i useful artifacts / 100 attempts. OpenClaw i szeroka równoległość pozostają za tą bramką.

T24 i aktuacja pozostają odroczone. Nie dodano tabel D1 ani komórek; 12 manifestów pozostaje zgodnych.
