# hermes_work_queue

Komorka pierwszej kolejki prac agentow (T18, dawniej H3). 5 jobow w seed_queue.json: repo_scout_daily, handoff_builder_after_commit, resource_scout_triage, execution_pack_draft_generator, audit_reviewer_before_pr.

## Zasady bezpieczenstwa

- Kazdy job ma no_auto_merge=true + no_direct_push=true.
- next_disabled=true - agent nie laczy jobow auto-chained.
- Konwencja: T<n> jest linearna; handoff_builder szanuje konwencje T<n>.
- Security audit przed PR - rejected jezeli wykryje `physical_actuation`, `auto_merge` albo `direct_push_main` w artifact.

## Uruchomienie

```bash
python3 hermes_work_queue/validate_queue.py
```
