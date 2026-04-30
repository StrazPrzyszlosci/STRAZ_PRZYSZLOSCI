# Canary Retro Template

## Cel

Ten template wypelnia wolontariusz i maintainer razem po pierwszym canary runie `Project 13`. Retro nie jest testem wolontariusza — to sprawdzenie, czy proces dziala, a nie czy czlowiek jest "dobry".

Retro nie udaje, ze wszystko poslo gladko. Jesli cos bylo zle, to wlasnie jest najwazniejsza informacja z canary.

---

## Dane canary

| Pole | Wartosc |
|------|---------|
| Data runu | BRAK — canary nie odbyl sie (NO-GO blocker receipt 2026-04-30) |
| Wolontariusz (login GitHub) | BRAK |
| Przydzial (np. VOL-P13-01) | BRAK |
| Pack | pack-project13-kaggle-enrichment-01 |
| PR (link) | BRAK |
| Wynik pre-flight (PASS/FAIL/MANUAL counts) | BRAK |
| Czy run zakonczony do konca? | N/A — canary nie startowal |
| Czy nastapil stop condition? | N/A — canary nie startowal |

> **Uwaga (zadanie 45, 2026-04-30):** Agent zapisal NO-GO blocker receipt, nie maintainer-signed decyzje. Wszystkie blokery C-1..C-5 w `CANARY_GO_LIVE_OPERATOR_PACKET.md` pozostaja OPEN. Retro template pozostaje pusty do wypelnienia po realnym canary. Receipt: `canary_go_no_go_receipt_2026-04-30.json`. |

---

## 1. Przed sesja: co dzialalo, co nie

### 1.1 Pre-flight check

- [ ] Skrypt `preflight_check.py` dal czytelny wynik
- [ ] Reczna checklist z `VOLUNTEER_PREFLIGHT_CHECKLIST.md` byla zrozumiala
- [ ] scope GITHUB_PAT udalo sie potwierdzic recznie
- [ ] quota YouTube/Gemini udalo sie potwierdzic recznie

**Co bylo niejasne w pre-flighcie:**

__DO_UZUPELNIENIA__

### 1.2 Runbook

- [ ] Runbook byl zrozumialy krok po kroku
- [ ] Instrukcja setupu sekretow byla wystarczajaca
- [ ] Instrukcja importu notebooka do Kaggle byla wystarczajaca
- [ ] Instrukcja pushu do forka byla wystarczajaca

**Co bylo niejasne w runbooku:**

__DO_UZUPELNIENIA__

### 1.3 Terms of participation

- [ ] Terms byly zrozumiale
- [ ] Wolontariusz wiedzial, ze moze przerwac w dowolnym momencie
- [ ] Wolontariusz wiedzial, ze wynik moze zostac odrzucony

**Co bylo niejasne w terms:**

__DO_UZUPELNIENIA__

---

## 2. W trakcie sesji: co dzialalo, co nie

### 2.1 Notebook na Kaggle

- [ ] Notebook uruchomil sie bez bledow
- [ ] Wszystkie komorki zakonczyly sie w rozsadnym czasie
- [ ] Wersje pakietow na Kaggle byly kompatybilne
- [ ] Sekrety dzialaly poprawnie (GITHUB_PAT, YOUTUBE_API_KEY, GEMINI_API_KEY)

**Bledy i problemy podczas runu:**

__DO_UZUPELNIENIA__

### 2.2 Stop conditions

- [ ] Zadny stop condition nie zostal spelniony (run przeszedl calkowicie)
- [ ] Stop condition zostal spelniony: __DO_UZUPELNIENIA__
- [ ] Stop conditions byly zrozumiale — wolontariusz wiedzial, kiedy przerwac

**Czy stop condition dzialal zgodnie z oczekiwaniem:**

__DO_UZUPELNIENIA__

### 2.3 Artefakty

- [ ] `processed_videos.json` powstal
- [ ] `results/test_db.jsonl` powstal
- [ ] `results/inventree_import.jsonl` powstal
- [ ] `results/ecoEDA_inventory.csv` powstal
- [ ] `reports/last_run_summary.md` powstal
- [ ] `reports/rebuild_autonomous_outputs_report.md` powstal
- [ ] `reports/rebuild_autonomous_outputs_skipped.jsonl` powstal

**Ktore artefakty brakuja i dlaczego:**

__DO_UZUPELNIENIA__

### 2.4 Fork flow i PR

- [ ] Push do forka dzialal
- [ ] PR moglem otworzyc bez problemu
- [ ] PR_TEMPLATE.md byl zrozumialy
- [ ] Helper dopiecia Artifact dzialal

**Co bylo niejasne w fork flow i PR:**

__DO_UZUPELNIENIA__

---

## 3. Po sesji: review i komunikacja

### 3.1 Review

- [ ] Reviewer odpowiedzial w rozsadnym czasie
- [ ] REVIEW_CHECKLIST.md byl uzyty
- [ ] Decyzja review byla zrozumiala
- [ ] Feedback byl konstruktywny

**Co bylo niejasne w review:**

__DO_UZUPELNIENIA__

### 3.2 Komunikacja z maintainerem

- [ ] Kanal komunikacji dzialal
- [ ] Czas odpowiedzi byl akceptowalny
- [ ] Wolontariusz nie czul sie zostawiony sam sobie

**Co bylo niejasne w komunikacji:**

__DO_UZUPELNIENIA__

---

## 4. Tarcie onboardingowe

Wypisz miejsca, gdzie wolontariusz musial "myslec" albo "zgadywac" zamiast postepowac za instrukcja:

| Krok runbooka | Co bylo niejasne | Co by pomoglo |
|---------------|-----------------|---------------|
| __DO_UZUPELNIENIA__ | __DO_UZUPELNIENIA__ | __DO_UZUPELNIENIA__ |

---

## 5. Zaskoczenia

Czy wszystko poszlo zgodnie z opisem, czy bylo cos, czego dokumenty nie przewidywaly?

__DO_UZUPELNIENIA__

---

## 6. Rekomendacje wolontariusza

Co wolontariusz polecilby zmienic, zanim kolejna osoba wejdzie w proces?

1. __DO_UZUPELNIENIA__
2. __DO_UZUPELNIENIA__
3. __DO_UZUPELNIENIA__

---

## 7. Rekomendacje maintainera

Co maintainer polecilby zmienic na podstawie tego canary?

1. __DO_UZUPELNIENIA__
2. __DO_UZUPELNIENIA__
3. __DO_UZUPELNIENIA__

---

## 8. Decyzja: czy otwierac run dla szerszego krgu

- [ ] Tak — proces jest gotowy na kolejnego wolontariusza
- [ ] Tak z poprawkami — po naniesieniu ponizszych zmian
- [ ] Nie — proces wymaga wiecej niz drobnych poprawek

**Uzasadnienie:**

__DO_UZUPELNIENIA__

**Poprawki do naniesienia przed kolejnym runem:**

__DO_UZUPELNIENIA__

---

## 9. Co zostalo otwarte

Rzeczy, ktore canary potwierdzil jako niewiadome albo nie do zasymulowania bez realnego wolontariusza:

1. __DO_UZUPELNIENIA__
2. __DO_UZUPELNIENIA__
3. __DO_UZUPELNIENIA__

---

## Zrodla

- `PROJEKTY/13_baza_czesci_recykling/docs/CANARY_PILOT_PACKET.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/VOLUNTEER_PREFLIGHT_CHECKLIST.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/VOLUNTEER_FALLBACK_GUIDE.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/VOLUNTEER_TERMS_OF_PARTICIPATION.md`
- `PROJEKTY/13_baza_czesci_recykling/execution_packs/pack-project13-kaggle-enrichment-01/RUNBOOK.md`
