"""Measured pilot outcomes. Human acceptance is never inferred from model output."""
import argparse
import json
from pathlib import Path


def measure(state_dir):
    root = Path(state_dir)
    runs = [json.loads(p.read_text()) for p in root.glob('runs/*/run_receipt.json')]
    events = [json.loads(line) for p in root.glob('runs/*/traces.jsonl') for line in p.read_text().splitlines() if line.strip()]
    attempts = [e for e in events if e.get('type') == 'node_result']
    ledger = json.loads((root / 'quota_ledger.json').read_text()) if (root / 'quota_ledger.json').exists() else {'daily': {}}
    decisions = [json.loads(line) for line in (root / 'decisions.jsonl').read_text().splitlines()] if (root / 'decisions.jsonl').exists() else []
    labels = [json.loads(line) for line in (root / 'labels.jsonl').read_text().splitlines()] if (root / 'labels.jsonl').exists() else []
    accepted = [r for r in runs if r.get('human_accepted') is True]
    reviewed = [r for r in runs if isinstance(r.get('human_accepted'), bool)]
    counted = sum(ledger['daily'].values())
    known_ids = {d['id'] for d in decisions}

    # Strona ewolucji (T63): zwalidowane artefakty, review, duplikaty,
    # czas i wywołania na propozycję. Brak danych = jawne None.
    evo_receipts = [json.loads(p.read_text()) for p in root.glob('evolution_queue/*/evolution_receipt.json')]
    validated = [r for r in evo_receipts if r.get('validation_ok') and r.get('security_ok') and r.get('execution_ok')]
    reviewed_evo = [r for r in evo_receipts if isinstance((r.get('review') or {}).get('verdict'), str) and r['review']['verdict'] != 'unreviewed']
    gate_passed = [r for r in evo_receipts if r.get('gate_ok')]
    index_path = root / 'evolution_index.json'
    index = json.loads(index_path.read_text()) if index_path.exists() else {}
    duplicate_attempts = sum(1 for row in index.values() if row.get('attempts', 0) > 1)
    evo_calls = sum(1 for r in evo_receipts if r.get('executor') in {'direct_patch', 'hermes'})
    durations = [r.get('latency_ms') for r in evo_receipts if isinstance(r.get('latency_ms'), (int, float))]
    pubs = [json.loads(p.read_text()) for p in root.glob('publication_requests/*.json')]
    published = [p for p in pubs if p.get('status') == 'published']

    def _per_100(numerator, denominator):
        return round(100 * numerator / denominator, 2) if denominator else None

    return {'attempts_in_node_traces': len(attempts), 'attempts_in_daily_ledger': counted,
            'successful_calls': sum(bool(e.get('ok')) for e in attempts),
            'failed_calls': sum(not e.get('ok') for e in attempts),
            'runs': len(runs), 'successful_runs': sum(r.get('status') == 'ok' for r in runs),
            'false_successes': sum(r.get('status') == 'ok' and bool(r.get('blocked')) for r in runs),
            'human_accepted_artifacts': len(accepted),
            'human_acceptance_rate': len(accepted) / len(reviewed) if reviewed else None,
            'useful_artifacts_per_100_attempts': _per_100(len(accepted), counted),
            'feedback_coverage': len({x['decision_id'] for x in labels} & known_ids) / len(known_ids) if known_ids else None,
            'evolution': {
                'receipts': len(evo_receipts),
                'validated_artifacts': len(validated),
                'validated_per_100_producer_calls': _per_100(len(validated), evo_calls),
                'gate_passed': len(gate_passed),
                'reviewed_evo': len(reviewed_evo),
                'positive_review_share': (sum(r['review']['verdict'] == 'pass' for r in reviewed_evo) / len(reviewed_evo)) if reviewed_evo else None,
                'duplicate_attempt_targets': duplicate_attempts,
                'producer_calls': evo_calls,
                'avg_producer_latency_ms': round(sum(durations) / len(durations)) if durations else None,
                'published_proposals': len(published),
                'calls_per_published_proposal': _per_100(evo_calls, len(published)) if published else None,
                'missing_data': [name for name, value in {
                    'labels': labels, 'validated_artifacts': validated,
                    'reviewed_evo': reviewed_evo, 'published': published}.items() if not value],
            },
            'policy': 'suggest-only', 'auto_applied': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--state-dir', type=Path, required=True)
    args = parser.parse_args()
    report = measure(args.state_dir)
    (args.state_dir / 'pilot_metrics.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False))
