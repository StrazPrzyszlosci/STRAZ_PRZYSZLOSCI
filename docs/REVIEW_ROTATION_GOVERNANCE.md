# Review Rotation Governance

## Cel dokumentu

Ten dokument opisuje minimalny model governance dla review i approval w Strazy Przyszlosci.

Jego zadaniem nie jest zbudowanie ciezkiej biurokracji. Ma ograniczac trzy konkretne ryzyka:

- koncentracje review w zbyt waskiej grupie osob,
- ciche samo-zatwierdzanie zmian przez autorow albo ich najblizszych wspolpracownikow,
- promocje workflowow i artefaktow bez jawnego polaczenia z `IntegrityRiskAssessment`, `ReadinessGate` i `Approval`.

To jest baseline dla obecnego etapu organizacji, w ktorym zespol reviewerow jest jeszcze maly, a czesc pracy wraca przez wolontariuszy i lokalnych agentow.

## Zakres

Dokument dotyczy:

- review `Pull Request`,
- review artefaktow powstalych po `Run`,
- approval promocji do kanonicznej bazy wiedzy,
- approval workflowow i execution packow,
- publicznych runow wolontariackich i wynikajacych z nich review.

Nie dotyczy jeszcze pelnej struktury personalnej organizacji ani formalnych uprawnien poza repo.

## Role

### `author_or_operator`

Osoba albo duet `wolontariusz + lokalny agent`, ktory uruchamia pack, przygotowuje artefakt albo otwiera `PR`.

### `pack_reviewer`

Reviewer ocenia:

- czy wynik spelnia acceptance criteria packa,
- czy provenance jest jawne,
- czy diff jest reviewowalny,
- czy nie miesza etapow lancucha wbrew kontraktowi.

### `integrity_reviewer`

Reviewer ocenia:

- czy zmiana nie omija jawnego review,
- czy nie wzmacnia `private_capture`, `volunteer_work_appropriation`, `opaque_approval_path`, `vendor_lock_in` albo podobnych sygnalow,
- czy wymagany `IntegrityRiskAssessment` istnieje i odpowiada realnej zmianie.

Przy mniejszym zespole ta rola moze byc czasowo pelniona przez maintainera niebedacego autorem zmiany.

### `approver`

Osoba wydajaca jawne `Approval` dla:

- promocji do katalogu kanonicznego,
- promocji workflowu,
- merge zmian o srednim lub wysokim ryzyku,
- pierwszych publicznych runow wolontariackich.

`Approver` nie powinien byc jednoczesnie jedynym `pack_reviewer` tej samej zmiany.

### `review_coordinator`

Lekka rola operacyjna potrzebna glownie przy publicznych runach wolontariackich.

Koordynator:

- wyznacza reviewerow przed uruchomieniem pilota,
- pilnuje, zeby review nie utknelo w jednej osobie,
- zapisuje wyjatki od rotacji, jesli zespol jest chwilowo zbyt maly.

Na obecnym etapie te role moze pelnic maintainer prowadzacy dany pilot.

## Twarde reguly

1. Autor zmiany nie zatwierdza sam swojej promocji do katalogu, workflowu ani deploymentu.
2. Ta sama osoba nie powinna byc jednoczesnie autorem, jedynym reviewerem i approverem tej samej zmiany.
3. Jesli istnieje wiecej niz jeden kwalifikowany reviewer, `pack_reviewer` dla tego samego packa nie powinien powtarzac sie wiecej niz dwa razy z rzedu.
4. Zmiana, ktora modyfikuje zasady review, approval, prawa dostepu albo sciezke pushu, wymaga osobnego `IntegrityRiskAssessment`.
5. Zmiana promujaca artefakt do kanonicznej bazy wiedzy musi przejsc przez jawny `ReadinessGate(review_ready)` przed `Approval`.
6. Zmiana o istotnym ryzyku governance musi przejsc przez `ReadinessGate(integrity_ready)` albo rownowazna jawna ocene integrity przed merge.
7. Publiczny wynik wolontariusza nie moze byc mergowany poza `fork -> PR -> review`, chyba ze powstanie osobna, jawnie opisana polityka awaryjna.

## Baseline model rotacji

Na obecnym etapie rekomendowany jest model lekki, bo organizacja nadal buduje pule reviewerow.

### Dla zwyklych zmian dokumentacyjnych i lekkich workflowow

- 1 `pack_reviewer`,
- 1 `approver` niebedacy autorem,
- `integrity_reviewer` tylko gdy zmiana dotyka governance, provenance, dostepu albo pracy wolontariuszy.

### Dla promotion do katalogu, execution packow i publicznych runow

- 1 `pack_reviewer`,
- 1 `integrity_reviewer` albo jawnie wskazany maintainer pelniacy te role,
- 1 `approver`,
- role powinny byc rozdzielone, jesli pozwala na to dostepna pula ludzi.

### Dla hardware runtime, deploymentow i sterowania swiatem fizycznym

Minimalny model powinien byc ostrzejszy:

- 1 reviewer merytoryczny,
- 1 reviewer integrity lub bezpieczenstwa,
- 1 approver,
- brak self-approval,
- brak merge bez jawnego bench testu albo raportu walidacyjnego.

Ten ostrzejszy model bedzie potrzebny dla przyszlych packow inspirowanych `Blueprint.am` i `ESP-Claw`.

## Wyjatki od rotacji

Repo moze czasowo nie miec wystarczajacej liczby reviewerow. Wtedy dopuszczalny jest tryb wyjatkowy, ale tylko jawnie:

- `review_coordinator` zapisuje w PR albo raporcie `rotation_exception`,
- wyjatek opisuje, czemu nie bylo alternatywnego reviewera,
- wyjatek nie znosi zakazu self-approval dla zmian sredniego i wysokiego ryzyka,
- po merge trzeba dopisac follow-up, jak zmniejszyc zaleznosc od jednej osoby.

Wyjatki nie powinny stac sie domyslnym trybem pracy.

## Zwiazek z encjami organizacji

### `IntegrityRiskAssessment`

Powinien byc wymagany, gdy zmiana:

- dotyka pracy wolontariuszy,
- zmienia sciezke review albo approval,
- otwiera nowy execution surface,
- moze promowac wynik do katalogu kanonicznego bez wystarczajacego provenance,
- dodaje hardware runtime albo deployment do swiata fizycznego.

### `ReadinessGate`

Minimalnie rozrozniaj:

- `review_ready`: artefakt jest czytelny, ma provenance i acceptance criteria,
- `integrity_ready`: ryzyka governance i public-interest zostaly jawnie ocenione,
- `pack_ready`: execution surface istnieje i da sie go uruchomic.

### `Approval`

`Approval` powinno wskazywac:

- kto byl `pack_reviewer`,
- kto byl `integrity_reviewer`, jesli dotyczy,
- kto wydal approval,
- jaki jest zakres approval (`knowledge_base_promotion`, `workflow_promotion`, `pilot_run`, `hardware_runtime`).

## Minimalny workflow review

```text
Artifact albo PR
  -> pack review
  -> ReadinessGate(review_ready)
  -> IntegrityRiskAssessment (jesli dotyczy)
  -> ReadinessGate(integrity_ready) albo jawny zapis "not required"
  -> Approval
  -> merge albo promotion
```

To ma byc jawny lancuch odpowiedzialnosci, a nie cicha praktyka ustalana ad hoc w komentarzach.

## Model dla pierwszego publicznego runu wolontariackiego

Przed pierwszym publicznym pilotem `Project 13` trzeba nazwac trzy role:

- `primary_pack_reviewer`,
- `backup_reviewer` albo `integrity_reviewer`,
- `approver`.

Nie trzeba od razu budowac duzego komitetu. Trzeba natomiast uniknac sytuacji, w ktorej ten sam maintainer:

- instruuje wolontariusza,
- odbiera wynik,
- sam wydaje approval,
- samodzielnie merge'uje bez jawnego sladu.

Dlatego pierwszy publiczny run powinien isc w modelu `controlled pilot`, z jawnym przydzialem reviewerow przed uruchomieniem notebooka.

## Dwa warianty docelowe

### Wariant A: lekka rotacja operacyjna

Najlepszy na teraz.

- prosty round-robin reviewerow,
- limit dwoch kolejnych review tego samego packa przez jedna osobe,
- jawne wyjatki od rotacji,
- jeden approver niebedacy autorem.

### Wariant B: twardsza rotacja dla packow krytycznych

Potrzebny przy hardware runtime, deploymentach i alokacji zasobow.

- rozdzielony reviewer merytoryczny i integrity reviewer,
- approver nie jest jednoczesnie glownym reviewerem,
- promotion do hardware albo deploymentu wymaga bench reportu,
- brak merge bez domknietego `integrity_ready`.

Rekomendacja na obecny etap:

- wdrozyc od razu wariant A jako baseline dla calego repo,
- stosowac wariant B dla packow o podwyzszonym ryzyku, zwlaszcza przyszlego runtime `ESP32`.

## Otwarte decyzje dla maintainerow

- kto w praktyce wchodzi do pierwszej puli reviewerow dla `Project 13`,
- czy limit dwoch review z rzedu ma byc liczony per pack, czy per caly projekt,
- od jakiego progu hardware runtime uznajemy pack za wymagajacy wariantu B,
- czy `Approval` ma byc zapisywany od razu jako osobny rekord przy pierwszym publicznym pilocie, czy dopiero po ustabilizowaniu procesu.
