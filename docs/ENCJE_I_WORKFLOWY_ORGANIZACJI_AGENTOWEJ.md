# Encje i Workflowy Organizacji Agentowej

## Cel dokumentu

Ten dokument zamienia plan rozwoju organizacji agentowej na **kanoniczny model encji i workflowow**, ktory mozna dalej mapowac na:

- pliki w repozytorium,
- rekordy JSON,
- przyszle tabele D1 lub SQLite,
- execution packi dla wolontariuszy,
- review i approval maintainera.

Robocza mapa tych encji do realnych tabel znajduje sie tutaj:

- [docs/MAPOWANIE_ENCJI_ORGANIZACJI_DO_D1_I_SQLITE.md](MAPOWANIE_ENCJI_ORGANIZACJI_DO_D1_I_SQLITE.md)
- [docs/REVIEW_ROTATION_GOVERNANCE.md](REVIEW_ROTATION_GOVERNANCE.md)

Kanoniczny schemat tych bytow znajduje sie tutaj:

- [schemas/organization_agent_v1.yaml](../schemas/organization_agent_v1.yaml)

Przykladowe rekordy znajduja sie tutaj:

- [data/sample/organization_resource_record.json](../data/sample/organization_resource_record.json)
- [data/sample/organization_potential_dossier.json](../data/sample/organization_potential_dossier.json)
- [data/sample/organization_capability_gap.json](../data/sample/organization_capability_gap.json)
- [data/sample/organization_experiment.json](../data/sample/organization_experiment.json)
- [data/sample/organization_execution_pack.json](../data/sample/organization_execution_pack.json)
- [data/sample/organization_task.json](../data/sample/organization_task.json)
- [data/sample/organization_run.json](../data/sample/organization_run.json)
- [data/sample/organization_artifact.json](../data/sample/organization_artifact.json)
- [data/sample/organization_integrity_risk_assessment.json](../data/sample/organization_integrity_risk_assessment.json)
- [data/sample/organization_approval.json](../data/sample/organization_approval.json)
- [data/sample/organization_readiness_gate.json](../data/sample/organization_readiness_gate.json)

## Minimalny zestaw encji

### `ResourceRecord`

Opisuje zasob wykryty przez organizacje.

To moze byc:

- elektroodpad,
- donor hardware,
- wolontariusz z kontem `Kaggle`,
- darmowa moc obliczeniowa,
- zewnetrzne repozytorium traktowane jako wzorzec RAG,
- lokalna energia, przestrzen albo logistyka,
- zbior danych lub kanal sygnalow.

### `PotentialDossier`

To podstawowa encja decyzyjna. Oprocz efektu, kosztu i czasu do rezultatu musi opisywac rowniez:

- ryzyka dla interesu wspolnego,
- mozliwe punkty przechwycenia zasobow,
- ryzyko centralizacji kontroli,
- ryzyko zawlaszczenia efektow pracy wolontariuszy.

### `CapabilityGap`

To encja opisujaca bariere miedzy obecnym stanem a stanem potrzebnym do kolejnego kroku.

Najczestsze typy:

- brak danych,
- brak workflowu,
- brak tooling,
- brak hardware,
- brak walidacji,
- brak gotowosci organizacyjnej.

### `Experiment`

To najmniejsza jednostka uczenia sie organizacji. Ma zmniejszac niepewnosc, a nie tylko produkowac kolejne artefakty.

### `ExecutionPack`

To kanoniczny pakiet pracy dla czlowieka i lokalnego agenta.

Poza celem, RAG i acceptance criteria powinien zawierac:

- `safety_notes`,
- `misuse_risks`,
- opis tego, jak unikac zawlaszczenia wyniku, ukrytego pushu do prywatnych zasobow albo niejawnej promocji.

### `Task`

To konkretne zlecenie uruchomienia `ExecutionPack`.

### `Run`

To konkretne uruchomienie zadania z jawnym srodowiskiem, czasem i logami.

### `Artifact`

To rezultat pracy powstaly po `Run`.

Moze nim byc:

- `Pull Request`,
- raport,
- dataset,
- update katalogu,
- output notebooka,
- projekt hardware,
- plan wdrozenia.

### `IntegrityRiskAssessment`

To encja review sprawdzajaca, czy zmiana nie wspiera zjawisk niekorzystnych dla ogolu.

Ma sluzyc do analizy:

- nepotyzmu,
- korupcji,
- zawlaszczenia wspolnych zasobow,
- ukrytego prywatnego przechwycenia efektow pracy,
- niejawnej centralizacji decyzji,
- omijania jawnego review,
- vendor lock-in i innych form uzaleznienia od waskiego interesu.

Ta encja moze dotyczyc:

- zmiany w kodzie,
- workflowu,
- zasad organizacyjnych,
- alokacji zasobow,
- deploymentu.

### `Approval`

To jawna decyzja review. `Approval` nie powinien byc wydawany dla istotnych zmian bez odniesienia do `IntegrityRiskAssessment`.

`Approval` powinno tez byc osadzone w jawnej polityce reviewer roles i rotacji review, a nie tylko w nieformalnym zwyczaju maintainera.

### `ReadinessGate`

To lekka bramka przejscia miedzy etapami. Poza klasycznym `review_ready` i `deployment_ready` powinna istniec rowniez bramka:

- `integrity_ready`

czyli potwierdzenie, ze zmiana przeszla analize zjawisk niekorzystnych dla ogolu.

## Kanoniczny przeplyw encji

Najprostszy przeplyw organizacji powinien wygladac tak:

```text
sygnal -> ResourceRecord -> PotentialDossier -> CapabilityGap -> Experiment ->
ExecutionPack -> Task -> Run -> Artifact -> IntegrityRiskAssessment ->
ReadinessGate(integrity_ready) -> Approval
```

Po drodze moga pojawiac sie inne `ReadinessGate`, na przyklad `pack_ready` lub `review_ready`.

## Workflow 1. Resource scouting i ranking

Cel:

- wykryc wartosciowy zasob lub okazje,
- ocenic, czy warto inwestowac dalsza energie organizacji.

Przeplyw:

```text
sygnal -> ResourceRecord -> PotentialDossier -> ReadinessGate(potential_review)
```

W tym miejscu trzeba analizowac nie tylko potencjal techniczny i ekonomiczny, ale tez to, czy kierunek nie tworzy zbyt latwej drogi do zawlaszczenia wspolnego efektu przez waska grupe.

## Workflow 2. Drabina kompetencji

Cel:

- rozbic wybrany kierunek na konkretne bariery i male kroki.

Przeplyw:

```text
PotentialDossier -> CapabilityGap -> Experiment -> ReadinessGate(experiment_ready)
```

Tu nalezy uwzgledniac rowniez bariery organizacyjne:

- brak transparentnosci,
- zbyt waskie grono reviewerow,
- brak sladu pochodzenia danych i decyzji.

## Workflow 3. Wolontariusz + agent jako warstwa wykonawcza

Cel:

- zamienic eksperyment lub barriere w zadanie gotowe do uruchomienia.

Przeplyw:

```text
Experiment albo CapabilityGap -> ExecutionPack -> Task -> Run -> Artifact
```

Najwazniejsza zasada:

- `ExecutionPack` musi byc na tyle dobry, aby nowy wolontariusz z lokalnym agentem mogl dowiezc wynik bez stalego wsparcia maintainera,
- a jednoczesnie na tyle jawny, aby wynik nie mogl zostac latwo ukryty, przechwycony albo przypisany niewlasciwej osobie.

## Workflow 4. Analiza zjawisk niekorzystnych dla ogolu

Cel:

- sprawdzic, czy kod, workflow, deployment albo decyzja organizacyjna nie wzmacnia zjawisk szkodliwych dla interesu wspolnego.

Przeplyw:

```text
Artifact albo ExecutionPack albo DeploymentPlan -> IntegrityRiskAssessment ->
ReadinessGate(integrity_ready)
```

Przykladowe sygnaly ryzyka:

- `nepotism`,
- `corruption`,
- `private_capture`,
- `volunteer_work_appropriation`,
- `opaque_approval_path`,
- `privileged_access_without_audit`,
- `vendor_lock_in`,
- `provenance_tampering`.

Ta analiza powinna byc wykonywana dla zmian, ktore:

- wplywaja na rozdzial zasobow,
- zmieniaja zasady approval,
- zmieniaja sciezki review,
- tworza nowe kanaly dostepu do wspolnych danych lub hardware,
- moga przekierowac wynik pracy spolecznosci do prywatnego interesu.

## Workflow 5. Review, approval i promocja

Cel:

- nie wpuszczac automatycznie wszystkiego do kanonicznej bazy wiedzy i do wdrozen.

Przeplyw:

```text
Artifact -> ReadinessGate(review_ready) -> IntegrityRiskAssessment ->
ReadinessGate(integrity_ready) -> Approval
```

Mozliwe decyzje:

- `approved`,
- `rejected`,
- `needs_changes`,
- `deferred`.

Mozliwe zakresy approval:

- `knowledge_base_promotion`,
- `workflow_promotion`,
- `pilot_run`,
- `hardware_runtime`,
- `deployment`,
- `field_action`,
- `hardware_build`,
- `budget_spend`.

## Workflow 6. Petla optymalizacji

Cel:

- poprawiac procesy dopiero wtedy, gdy istnieja logi, provenance i decyzje review.

Przeplyw:

```text
Run + Artifact + IntegrityRiskAssessment + Approval ->
analiza jakosci -> nowy CapabilityGap albo nowy ExecutionPack
```

Nie optymalizujemy tylko szybkosci i kosztu. Optymalizujemy rowniez:

- transparentnosc,
- odpornosc na przechwycenie procesu,
- jakosc review,
- zdolnosc wykrywania zjawisk szkodliwych dla ogolu.

## Minimalne statusy operacyjne

### `PotentialDossier.candidate_status`

- `draft`
- `ranked`
- `pilot_ready`
- `active`
- `paused`
- `archived`

### `CapabilityGap.status`

- `open`
- `exploring`
- `partially_addressed`
- `ready_for_pack`
- `closed`

### `ExecutionPack.status`

- `draft`
- `ready`
- `active`
- `retired`

### `Run.status`

- `queued`
- `running`
- `succeeded`
- `failed`
- `cancelled`
- `needs_review`

### `IntegrityRiskAssessment.status`

- `pass`
- `needs_changes`
- `blocked`

### `Approval.decision`

- `approved`
- `rejected`
- `needs_changes`
- `deferred`

## Jak mapowac ten model na repozytorium

Na teraz ten model powinien zyc jako:

- schemat w `schemas/`,
- sample records w `data/sample/`,
- dokumentacja i runbooki w `docs/`,
- execution packi w projektach i przyszlych katalogach workflowow.

W kolejnym kroku mozna to mapowac na:

- tabele `D1` lub `SQLite`,
- issue templates,
- automaty publikujace packi,
- raporty rankingowe,
- dashboard maintainera,
- automatyczne checklisty integrity review dla PR i deploymentow.

## Co z tego wynika praktycznie

Od tej chwili nowe kierunki mozna opisywac nie ogolnym tekstem, lecz zestawem bytow:

1. `ResourceRecord` mowi, jaki zasob wykryto.
2. `PotentialDossier` mowi, dlaczego ten kierunek ma lub nie ma sensu.
3. `CapabilityGap` mowi, co blokuje przejscie dalej.
4. `Experiment` mowi, jak zmniejszyc niepewnosc.
5. `ExecutionPack` mowi, co dokladnie ma zrobic czlowiek i agent.
6. `Task` i `Run` mowia, co zostalo uruchomione.
7. `Artifact` mowi, co powstalo.
8. `IntegrityRiskAssessment` mowi, czy wynik albo zmiana nie szkodzi interesowi wspolnemu.
9. `Approval` mowi, czy wynik wolno promowac dalej.

To jest minimalny operacyjny model, ktory pozwala zamienic organizacje agentowa z poziomu idei na poziom procesu.
