# D1/SQLite Query Cookbook

## Cel dokumentu

Ten cookbook zamienia warstwe projekcji D1/SQLite (zbudowana w zadaniu 01) na realne narzedzie operacyjne. Pokazuje, jak pytac o stan encji, packow, runow i approval — tak, aby maintainerzy i agenci mogli szybko odpowiedziec na pytania operacyjne bez recznego przegladania plikow JSON.

Zalezy od: migracji `cloudflare/migrations/0012_organization_agent_entities.sql` i wyniku syncu z `pipelines/sync_organization_entities_to_sqlite.py`.

## Jak uzyc cookbooka

1. Zsynchronizuj baze:
   ```bash
   python3 pipelines/sync_organization_entities_to_sqlite.py --db-path /tmp/org.sqlite3
   ```
2. Odpalaj query z tego cookbooka przez `sqlite3` lub helper `pipelines/org_lookup.py`.
3. Wszystkie query sa kompatybilne z SQLite i Cloudflare D1.

---

## 1. Zasoby (ResourceRecord)

### 1.1 Wszystkie aktywne zasoby

```sql
SELECT resource_id, resource_kind, title, status, expected_leverage
FROM organization_resource_records
WHERE status = 'active'
ORDER BY discovered_at DESC;
```

### 1.2 Zasoby po rodzaju

```sql
SELECT resource_kind, COUNT(*) AS cnt
FROM organization_resource_records
GROUP BY resource_kind
ORDER BY cnt DESC;
```

### 1.3 Zasoby o najwyzszej dzwigni

```sql
SELECT resource_id, title, expected_leverage, access_model
FROM organization_resource_records
WHERE expected_leverage = 'high'
ORDER BY discovered_at DESC;
```

### 1.4 Zasoby czekajace na review

```sql
SELECT resource_id, title, last_reviewed_at
FROM organization_resource_records
WHERE last_reviewed_at IS NULL
   OR last_reviewed_at < datetime('now', '-30 days')
ORDER BY discovered_at ASC;
```

### 1.5 Szczegol rekordu zasobu z payloadem

```sql
SELECT resource_id, title, payload_json
FROM organization_resource_records
WHERE resource_id = 'resource-kaggle-volunteers-01';
```

---

## 2. Dossiers (PotentialDossier)

### 2.1 Wszystkie dossiers posortowane po priorytecie

```sql
SELECT dossier_id, title, target_domain, candidate_status, overall_priority_score
FROM organization_potential_dossiers
ORDER BY overall_priority_score DESC;
```

### 2.2 Dossiers gotowe na pilot

```sql
SELECT dossier_id, title, overall_priority_score, recommended_action
FROM organization_potential_dossiers
WHERE candidate_status = 'pilot_ready'
ORDER BY overall_priority_score DESC;
```

### 2.3 Dossiers po domenie

```sql
SELECT target_domain, COUNT(*) AS cnt, ROUND(AVG(overall_priority_score), 2) AS avg_priority
FROM organization_potential_dossiers
GROUP BY target_domain
ORDER BY avg_priority DESC;
```

### 2.4 Dossiers z niskim priorytetem wymagajace rewizji

```sql
SELECT dossier_id, title, overall_priority_score, candidate_status
FROM organization_potential_dossiers
WHERE overall_priority_score < 0.5
ORDER BY overall_priority_score ASC;
```

---

## 3. Luki zdolnosci (CapabilityGap)

### 3.1 Wszystkie otwarte luki

```sql
SELECT gap_id, title, gap_kind, severity, status, dossier_id
FROM organization_capability_gaps
WHERE status NOT IN ('resolved', 'closed')
ORDER BY
  CASE severity WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
  created_at ASC;
```

### 3.2 Luki blokujace dany dossier

```sql
SELECT gap_id, title, severity, status, blocking_reason
FROM organization_capability_gaps
WHERE dossier_id = 'dossier-project13-resource-scouting-01'
  AND status NOT IN ('resolved', 'closed');
```

### 3.3 Luki gotowe na execution pack

```sql
SELECT gap_id, title, gap_kind, severity, dossier_id
FROM organization_capability_gaps
WHERE status = 'ready_for_pack'
ORDER BY
  CASE severity WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END;
```

### 3.4 Podsumowanie luk po typie

```sql
SELECT gap_kind, COUNT(*) AS cnt,
  SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) AS critical,
  SUM(CASE WHEN severity = 'high' THEN 1 ELSE 0 END) AS high,
  SUM(CASE WHEN severity = 'medium' THEN 1 ELSE 0 END) AS medium
FROM organization_capability_gaps
WHERE status NOT IN ('resolved', 'closed')
GROUP BY gap_kind
ORDER BY cnt DESC;
```

---

## 4. Eksperymenty (Experiment)

### 4.1 Eksperymenty powiazane z dana luka

```sql
SELECT experiment_id, status, hypothesis
FROM organization_experiments
WHERE gap_id = 'gap-project13-review-ready-artifacts-01';
```

### 4.2 Eksperymenty po statusie

```sql
SELECT status, COUNT(*) AS cnt
FROM organization_experiments
GROUP BY status
ORDER BY cnt DESC;
```

### 4.3 Eksperymenty gotowe do uruchomienia

```sql
SELECT experiment_id, hypothesis, gap_id
FROM organization_experiments
WHERE status = 'ready'
ORDER BY created_at ASC;
```

### 4.4 Lanuch: luka -> eksperymenty

```sql
SELECT g.gap_id, g.title AS gap_title, e.experiment_id, e.status AS experiment_status
FROM organization_capability_gaps g
LEFT JOIN organization_experiments e ON e.gap_id = g.gap_id
WHERE g.status NOT IN ('resolved', 'closed')
ORDER BY g.gap_id, e.created_at;
```

---

## 5. Execution Packi

### 5.1 Wszystkie packi po statusie

```sql
SELECT pack_id, title, status, execution_mode, target_output_kind
FROM organization_execution_packs
ORDER BY
  CASE status
    WHEN 'ready' THEN 0
    WHEN 'in_progress' THEN 1
    WHEN 'benchmarked' THEN 2
    WHEN 'review_ready' THEN 3
    ELSE 4
  END,
  created_at ASC;
```

### 5.2 Packi powiazane z konkretnym tematem (polimorficzne)

```sql
SELECT pack_id, title, execution_mode, status
FROM organization_execution_packs
WHERE linked_subject_kind = 'experiment'
  AND linked_subject_id = 'experiment-kaggle-review-ready-pack-01';
```

### 5.3 Packi gotowe do uruchomienia przez wolontariusza

```sql
SELECT pack_id, title, execution_mode, notebook_path, runbook_path
FROM organization_execution_packs
WHERE status = 'ready'
  AND execution_mode IN ('kaggle_notebook', 'colab_notebook', 'local_script')
ORDER BY created_at ASC;
```

### 5.4 Packi z linkage do zasobow (przez payload)

```sql
SELECT p.pack_id, p.title, p.status, json_extract(p.payload_json, '$.required_resources') AS resources
FROM organization_execution_packs p
WHERE json_extract(p.payload_json, '$.required_resources') IS NOT NULL;
```

### 5.5 Podsumowanie packow po trybie wykonania

```sql
SELECT execution_mode, COUNT(*) AS cnt,
  SUM(CASE WHEN status = 'ready' THEN 1 ELSE 0 END) AS ready,
  SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) AS in_progress
FROM organization_execution_packs
GROUP BY execution_mode
ORDER BY cnt DESC;
```

---

## 6. Zadania (Task)

### 6.1 Zadania dla konkretnego packa

```sql
SELECT task_id, assignee_mode, requested_by, status, created_at
FROM organization_tasks
WHERE pack_id = 'pack-project13-kaggle-enrichment-01'
ORDER BY created_at ASC;
```

### 6.2 Zadania po statusie

```sql
SELECT status, COUNT(*) AS cnt
FROM organization_tasks
GROUP BY status
ORDER BY cnt DESC;
```

### 6.3 Zadania wolontariackie czekajace na wykonawce

```sql
SELECT t.task_id, t.pack_id, p.title AS pack_title, t.assignee_mode, t.status
FROM organization_tasks t
JOIN organization_execution_packs p ON p.pack_id = t.pack_id
WHERE t.assignee_mode = 'volunteer_plus_agent'
  AND t.status IN ('submitted', 'open')
ORDER BY t.created_at ASC;
```

---

## 7. Runy

### 7.1 Wszystkie runy po statusie

```sql
SELECT status, COUNT(*) AS cnt
FROM organization_runs
GROUP BY status
ORDER BY cnt DESC;
```

### 7.2 Runy dla konkretnego packa z czasem trwania

```sql
SELECT run_id, operator_kind, environment_kind, status,
       started_at, ended_at,
       CASE WHEN ended_at IS NOT NULL
         THEN CAST((julianday(ended_at) - julianday(started_at)) * 24 * 60 AS INTEGER)
         ELSE NULL
       END AS duration_minutes
FROM organization_runs
WHERE pack_id = 'pack-project13-kaggle-enrichment-01'
ORDER BY started_at DESC;
```

### 7.3 Runy czekajace na review

```sql
SELECT r.run_id, r.pack_id, p.title AS pack_title, r.operator_kind, r.started_at
FROM organization_runs r
JOIN organization_execution_packs p ON p.pack_id = r.pack_id
WHERE r.status = 'needs_review'
ORDER BY r.started_at DESC;
```

### 7.4 Nieudane runy

```sql
SELECT run_id, pack_id, operator_kind, environment_kind, started_at, logs_ref
FROM organization_runs
WHERE status = 'failed'
ORDER BY started_at DESC;
```

### 7.5 Podsumowanie runow po srodowisku

```sql
SELECT environment_kind, COUNT(*) AS total,
  SUM(CASE WHEN status = 'needs_review' THEN 1 ELSE 0 END) AS needs_review,
  SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed,
  SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed
FROM organization_runs
GROUP BY environment_kind
ORDER BY total DESC;
```

---

## 8. Artefakty

### 8.1 Artefakty czekajace na review

```sql
SELECT a.artifact_id, a.artifact_kind, a.title, a.review_status,
       r.pack_id, a.created_at
FROM organization_artifacts a
JOIN organization_runs r ON r.run_id = a.run_id
WHERE a.review_status IN ('review_ready', 'pending_review')
ORDER BY a.created_at DESC;
```

### 8.2 Artefakty dla konkretnego runu

```sql
SELECT artifact_id, artifact_kind, title, storage_ref, review_status
FROM organization_artifacts
WHERE run_id = 'run-project13-kaggle-enrichment-01'
ORDER BY created_at ASC;
```

### 8.3 Artefakty po statusie review

```sql
SELECT review_status, COUNT(*) AS cnt
FROM organization_artifacts
GROUP BY review_status
ORDER BY cnt DESC;
```

### 8.4 Zaakceptowane artefakty nadajace sie do promocji

```sql
SELECT a.artifact_id, a.title, a.artifact_kind, a.storage_ref
FROM organization_artifacts a
WHERE a.review_status = 'approved'
ORDER BY a.created_at DESC;
```

### 8.5 Ostatnie artefakty z pelnym provenance

```sql
SELECT a.artifact_id, a.title, a.artifact_kind, a.review_status,
       r.run_id, r.pack_id, p.title AS pack_title
FROM organization_artifacts a
JOIN organization_runs r ON r.run_id = a.run_id
JOIN organization_execution_packs p ON p.pack_id = r.pack_id
ORDER BY a.created_at DESC
LIMIT 20;
```

---

## 9. Integrity Risk Assessments

### 9.1 Ostatnie oceny ryzyka

```sql
SELECT assessment_id, subject_kind, subject_id, risk_level, status, reviewer_role, assessed_at
FROM organization_integrity_risk_assessments
ORDER BY assessed_at DESC;
```

### 9.2 Oceny ryzyka dla konkretnego tematu (polimorficzne)

```sql
SELECT assessment_id, assessment_scope, risk_level, status, reviewer_role, assessed_at
FROM organization_integrity_risk_assessments
WHERE subject_kind = 'artifact'
  AND subject_id = 'artifact-project13-pr-01'
ORDER BY assessed_at DESC;
```

### 9.3 Wysokie i krytyczne ryzyka

```sql
SELECT assessment_id, subject_kind, subject_id, assessment_scope, risk_level, status
FROM organization_integrity_risk_assessments
WHERE risk_level IN ('high', 'critical')
  AND status != 'mitigated'
ORDER BY assessed_at DESC;
```

### 9.4 Podsumowanie ocen ryzyka po poziomie

```sql
SELECT risk_level, COUNT(*) AS cnt,
  SUM(CASE WHEN status = 'pass' THEN 1 ELSE 0 END) AS pass_cnt,
  SUM(CASE WHEN status = 'fail' THEN 1 ELSE 0 END) AS fail_cnt,
  SUM(CASE WHEN status = 'mitigated' THEN 1 ELSE 0 END) AS mitigated_cnt
FROM organization_integrity_risk_assessments
GROUP BY risk_level
ORDER BY
  CASE risk_level WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 ELSE 4 END;
```

---

## 10. Approvals

### 10.1 Ostatnie decyzje approval

```sql
SELECT approval_id, artifact_id, decision, approval_scope, reviewer_role, decided_at
FROM organization_approvals
ORDER BY decided_at DESC;
```

### 10.2 Approval dla konkretnego artefaktu

```sql
SELECT approval_id, decision, approval_scope, reviewer_role, decided_at
FROM organization_approvals
WHERE artifact_id = 'artifact-project13-pr-01'
ORDER BY decided_at DESC;
```

### 10.3 Odrzucone approvals

```sql
SELECT a.approval_id, a.artifact_id, a.decision, a.reviewer_role, a.decided_at,
       art.title AS artifact_title
FROM organization_approvals a
JOIN organization_artifacts art ON art.artifact_id = a.artifact_id
WHERE a.decision = 'rejected'
ORDER BY a.decided_at DESC;
```

### 10.4 Podsumowanie approvals po decyzji

```sql
SELECT decision, COUNT(*) AS cnt
FROM organization_approvals
GROUP BY decision
ORDER BY cnt DESC;
```

---

## 11. Readiness Gates

### 11.1 Wszystkie gates dla konkretnego tematu

```sql
SELECT gate_id, gate_kind, status, checked_at
FROM organization_readiness_gates
WHERE subject_kind = 'execution_pack'
  AND subject_id = 'pack-project13-kaggle-enrichment-01'
ORDER BY checked_at DESC;
```

### 11.2 Niespelnione gates

```sql
SELECT gate_id, subject_kind, subject_id, gate_kind, status, checked_at
FROM organization_readiness_gates
WHERE status != 'pass'
ORDER BY checked_at DESC;
```

### 11.3 Podsumowanie gates po rodzaju

```sql
SELECT gate_kind, COUNT(*) AS total,
  SUM(CASE WHEN status = 'pass' THEN 1 ELSE 0 END) AS pass_cnt,
  SUM(CASE WHEN status = 'fail' THEN 1 ELSE 0 END) AS fail_cnt
FROM organization_readiness_gates
GROUP BY gate_kind
ORDER BY total DESC;
```

---

## 12. Zapytania transwersalne (cross-entity)

### 12.1 Pelny lanuch: dossier -> gap -> experiment -> pack -> task -> run

```sql
SELECT
  d.dossier_id, d.title AS dossier_title,
  g.gap_id, g.title AS gap_title, g.severity,
  e.experiment_id, e.status AS experiment_status,
  p.pack_id, p.title AS pack_title, p.status AS pack_status,
  t.task_id, t.status AS task_status,
  r.run_id, r.status AS run_status
FROM organization_potential_dossiers d
LEFT JOIN organization_capability_gaps g ON g.dossier_id = d.dossier_id
LEFT JOIN organization_experiments e ON e.gap_id = g.gap_id
LEFT JOIN organization_execution_packs p ON p.linked_subject_kind = 'experiment' AND p.linked_subject_id = e.experiment_id
LEFT JOIN organization_tasks t ON t.pack_id = p.pack_id
LEFT JOIN organization_runs r ON r.pack_id = p.pack_id
ORDER BY d.overall_priority_score DESC, g.severity, p.created_at;
```

### 12.2 Artefakty z lanucha approval: artifact -> approval -> integrity

```sql
SELECT
  a.artifact_id, a.title AS artifact_title, a.review_status,
  ap.approval_id, ap.decision, ap.reviewer_role AS approval_reviewer,
  ira.assessment_id, ira.risk_level, ira.status AS integrity_status
FROM organization_artifacts a
LEFT JOIN organization_approvals ap ON ap.artifact_id = a.artifact_id
LEFT JOIN organization_integrity_risk_assessments ira
  ON ira.subject_kind = 'artifact' AND ira.subject_id = a.artifact_id
ORDER BY a.created_at DESC;
```

### 12.3 Dashboard portfela: stan wszystkich packow z gate'ami

```sql
SELECT
  p.pack_id, p.title, p.status AS pack_status,
  g.gate_kind, g.status AS gate_status,
  (SELECT COUNT(*) FROM organization_tasks t WHERE t.pack_id = p.pack_id) AS task_count,
  (SELECT COUNT(*) FROM organization_runs r WHERE r.pack_id = p.pack_id) AS run_count,
  (SELECT COUNT(*) FROM organization_artifacts a
   JOIN organization_runs r2 ON r2.run_id = a.run_id
   WHERE r2.pack_id = p.pack_id AND a.review_status = 'review_ready') AS review_ready_count
FROM organization_execution_packs p
LEFT JOIN organization_readiness_gates g
  ON g.subject_kind = 'execution_pack' AND g.subject_id = p.pack_id
ORDER BY
  CASE p.status
    WHEN 'ready' THEN 0 WHEN 'in_progress' THEN 1 WHEN 'review_ready' THEN 2 ELSE 3
  END;
```

### 12.4 Zasoby powiazane z dossier (przez payload linked_resources)

```sql
SELECT
  d.dossier_id, d.title AS dossier_title,
  r.resource_id, r.title AS resource_title, r.resource_kind, r.status
FROM organization_potential_dossiers d,
     json_each(json_extract(d.payload_json, '$.linked_resources')) AS lr
JOIN organization_resource_records r
  ON r.resource_id = json_extract(lr.value, '$.entity_id')
WHERE json_extract(lr.value, '$.entity_kind') = 'resource_record';
```

### 12.5 Szeroki przeglad: co jest zablokowane w organizacji

```sql
SELECT 'open_gap' AS blockage_kind, gap_id AS id, title, severity AS detail, status
FROM organization_capability_gaps
WHERE status NOT IN ('resolved', 'closed')

UNION ALL

SELECT 'failed_run', run_id, operator_kind, environment_kind, status
FROM organization_runs
WHERE status = 'failed'

UNION ALL

SELECT 'unapproved_artifact', artifact_id, title, review_status, artifact_kind
FROM organization_artifacts
WHERE review_status = 'rejected'

UNION ALL

SELECT 'failed_gate', gate_id, gate_kind, subject_id, status
FROM organization_readiness_gates
WHERE status = 'fail'

ORDER BY
  CASE detail WHEN 'critical' THEN 0 WHEN 'high' THEN 1 ELSE 2 END;
```

---

## 13. Query diagnostyczne

### 13.1 Spis wszystkich tabel z liczba rekordow

```sql
SELECT 'organization_resource_records' AS tbl, COUNT(*) FROM organization_resource_records
UNION ALL SELECT 'organization_potential_dossiers', COUNT(*) FROM organization_potential_dossiers
UNION ALL SELECT 'organization_capability_gaps', COUNT(*) FROM organization_capability_gaps
UNION ALL SELECT 'organization_experiments', COUNT(*) FROM organization_experiments
UNION ALL SELECT 'organization_execution_packs', COUNT(*) FROM organization_execution_packs
UNION ALL SELECT 'organization_tasks', COUNT(*) FROM organization_tasks
UNION ALL SELECT 'organization_runs', COUNT(*) FROM organization_runs
UNION ALL SELECT 'organization_artifacts', COUNT(*) FROM organization_artifacts
UNION ALL SELECT 'organization_integrity_risk_assessments', COUNT(*) FROM organization_integrity_risk_assessments
UNION ALL SELECT 'organization_approvals', COUNT(*) FROM organization_approvals
UNION ALL SELECT 'organization_readiness_gates', COUNT(*) FROM organization_readiness_gates;
```

### 13.2 Ostatnia aktualizacja (inserted_at / updated_at)

```sql
SELECT 'resource_records' AS tbl, MAX(updated_at) FROM organization_resource_records
UNION ALL SELECT 'dossiers', MAX(updated_at) FROM organization_potential_dossiers
UNION ALL SELECT 'capability_gaps', MAX(updated_at) FROM organization_capability_gaps
UNION ALL SELECT 'experiments', MAX(updated_at) FROM organization_experiments
UNION ALL SELECT 'execution_packs', MAX(updated_at) FROM organization_execution_packs
UNION ALL SELECT 'tasks', MAX(updated_at) FROM organization_tasks
UNION ALL SELECT 'runs', MAX(ended_at) FROM organization_runs
UNION ALL SELECT 'artifacts', MAX(updated_at) FROM organization_artifacts
UNION ALL SELECT 'integrity_risk', MAX(assessed_at) FROM organization_integrity_risk_assessments
UNION ALL SELECT 'approvals', MAX(decided_at) FROM organization_approvals
UNION ALL SELECT 'readiness_gates', MAX(checked_at) FROM organization_readiness_gates;
```

### 13.3 Sprawdzenie integralnosci FK: runs bez packa

```sql
SELECT r.run_id, r.pack_id
FROM organization_runs r
LEFT JOIN organization_execution_packs p ON p.pack_id = r.pack_id
WHERE p.pack_id IS NULL;
```

### 13.4 Sprawdzenie integralnosci FK: artifacts bez runa

```sql
SELECT a.artifact_id, a.run_id
FROM organization_artifacts a
LEFT JOIN organization_runs r ON r.run_id = a.run_id
WHERE r.run_id IS NULL;
```

---

## 14. Uwagi operacyjne

- Wszystkie query sa kompatybilne z SQLite 3.x i Cloudflare D1.
- `payload_json` zawiera pelny kanoniczny rekord; uzywaj `json_extract()` do dostepu do pol niepromowanych do kolumn.
- Zrodlem prawdy pozostaje repo (JSON, Markdown, PR). D1/SQLite to warstwa projekcji.
- Po kazdym syncu (`pipelines/sync_organization_entities_to_sqlite.py`) dane w bazie sa odswiezone przez upsert.
- Polimorficzne referencje (`subject_kind`/`subject_id`, `linked_subject_kind`/`linked_subject_id`) pozwalaja laczyc encje bez sztucznej hierarchii.
