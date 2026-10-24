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
    return {'attempts_in_node_traces': len(attempts), 'attempts_in_daily_ledger': counted,
            'successful_calls': sum(bool(e.get('ok')) for e in attempts),
            'failed_calls': sum(not e.get('ok') for e in attempts),
            'runs': len(runs), 'successful_runs': sum(r.get('status') == 'ok' for r in runs),
            'false_successes': sum(r.get('status') == 'ok' and bool(r.get('blocked')) for r in runs),
            'human_accepted_artifacts': len(accepted),
            'human_acceptance_rate': len(accepted) / len(reviewed) if reviewed else None,
            'useful_artifacts_per_100_attempts': 100 * len(accepted) / counted if counted else None,
            'feedback_coverage': len({x['decision_id'] for x in labels} & known_ids) / len(known_ids) if known_ids else None,
            'policy': 'suggest-only', 'auto_applied': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--state-dir', type=Path, required=True)
    args = parser.parse_args()
    report = measure(args.state_dir)
    (args.state_dir / 'pilot_metrics.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False))
