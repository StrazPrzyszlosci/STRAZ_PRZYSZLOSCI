# Terms of Participation Dla Wolontariuszy Project 13

## Cel

Ten dokument okresla minimalne warunki udzialu wolontariusza w publicznych runach `Project 13`. Nie jest to umowa prawna — to jawne porozumienie o tym, co wolontariusz wklada, co otrzymuje i jakie sa zasady.

---

## 1. Twoj wkład jest dobrowolny

- Decydujesz sam, czy chcesz uruchomic notebook na swoim koncie `Kaggle`.
- Decydujesz sam, czy chcesz zuzyc swoje darmowe limity obliczeniowe i API.
- Mozesz przerwac w dowolnym momencie bez podawania powodu.
- Nikt nie moze Ci nakazac kontynuacji ani sugerowac, ze "musisz" dokonczyc run.

---

## 2. Twoj wkład jest publiczny

- Fork repozytorium jest publiczny.
- Pull Request jest publiczny.
- Twoj commit widnieje w historii forka.
- Wyniki uruchomienia moga byc cytowane, linkowane i wykorzystywane w downstream artefaktach.

**Jesli nie chcesz, aby Twoj nick GitHub byl powiazany z wynikami, uzyj konta z anonimowym identyfikatorem.**

---

## 3. Twoj wynik moze zostac odrzucony

- Kazdy PR przechodzi przez review.
- Reviewer moze poprosic o zmiany, zadac wyjasnien albo odrzucic PR.
- Odrzucenie PR nie jest ocena Ciebie — to ocena wyniku pod katem jakosci danych i zgodnosci z kontraktem packa.
- Odrzucony PR zostaje w historii forka i nadal jest Twoim wkładem.

---

## 4. Twoje sekrety sa Twoje

- Ustawiasz sekrety (`GITHUB_PAT`, `YOUTUBE_API_KEY`, `GEMINI_API_KEY`) wlasnorecznie na swoim koncie `Kaggle`.
- Repozytorium nie przechowuje Twoich sekretow.
- Nie wolno zapisywac sekretow w kodzie, commitach, PR ani komentarzach.
- Koszt API ponosisz sam: inicjatywa nie zwraca kosztow poniesionych na klucze.

---

## 5. Twoja praca nie bedzie zawlaszczona

- Wynik Twojego runu wraca przez fork i PR, a nie przez bezposredni push do upstream.
- Wynik jest reviewowany przed merge.
- Provenance (kto uruchomil, kiedy, na jakim packu) jest jawne w rekordzie `Run`.
- Nie wolno podmieniac autora commita ani ukryc Twojego udzialu.

---

## 6. Nie gwarantujemy wsparcia na zywo

- Na obecnym etapie projekt nie ma pelnoetatowego supportu.
- Rekomendowany kanal zgloszenia problemu: GitHub Issue z labelka `volunteer-support`.
- Cel czasowy odpowiedzi: 48h roboczych, ale na obecnym etapie moze byc dluzszy.
- Twoj lokalny agent moze pomoc Ci na biezaco, ale nie zastapi maintainera.

---

## 7. Nie ponosisz odpowiedzialnosci za jakosc danych

- Notebook generuje dane automatycznie. Twoja rola to uruchomienie i weryfikacja, a nie reczne poprawianie wynikow.
- Jesli wynik zawiera bledy, to problem pipeline'u, a nie Twoj.
- Nie probuj recznie dopisywac ani modyfikowac artefaktow poza notebookiem.

---

## 8. Zasady zachowania

- Nie pushuj bezposrednio do upstream.
- Nie commituj sekretow, plikow tymczasowych ani pobranych materialow binarnych.
- Nie podmieniaj autora commita.
- Nie promuj wynikow bez raportu runu i jawnego PR.

---

## 9. Co dostajesz w zamian

- Uczestnictwo w budowie otwartej bazy czesci recyklingowych.
- Przyczynek do publicznie dostepnej wiedzy o odzyskiwaniu czesci elektronicznych.
- Doswiadczenie w pracy z agentami AI i pipeline'ami danych.
- Jawny slad Twojego udzialu w historii repozytorium.

---

## 10. Zmiany terms

- Jesli terms ulegna zmianie, nowe wersje beda commitowane do repozytorium.
- Wolontariusz jest zobowiazany do najnowszej wersji terms obowiazujacej w momencie jego runu.
- Zmiany terms nie obowiazuja retroaktywnie dla juz zmergowanych PR.

---

## Potwierdzenie

Nie musisz podpisywac tego dokumentu. Uruchomienie notebooka i otwarcie PR jest traktowane jako potwierdzenie, ze znasz i akceptujesz te warunki.

Jesli masz pytania, otworz Issue z labelka `volunteer-support`.

---

## Zrodla

- `PROJEKTY/13_baza_czesci_recykling/docs/MODEL_WOLONTARIACKICH_NOTEBOOKOW_KAGGLE.md`
- `PROJEKTY/13_baza_czesci_recykling/docs/PUBLIC_VOLUNTEER_RUN_READINESS.md`
- `docs/REVIEW_ROTATION_GOVERNANCE.md`
