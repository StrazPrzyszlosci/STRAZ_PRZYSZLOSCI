"""Durable task leases, retries and feedback. A receipt is committed only by its lease owner."""
from __future__ import annotations
import fcntl
import json
import os
import time
import uuid
from contextlib import contextmanager
from pathlib import Path


class EvolutionStore:
    TERMINAL = {'ready', 'published', 'accepted', 'rejected', 'simulated'}

    def __init__(self, root, *, clock=time.time, max_attempts=3, retry_seconds=60, lease_seconds=1200):
        self.root = Path(root)
        self.clock, self.max_attempts = clock, max_attempts
        self.retry_seconds, self.lease_seconds = retry_seconds, lease_seconds

    @contextmanager
    def transaction(self):
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / 'evolution_index.json'
        with (self.root / 'evolution_index.lock').open('a+') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            data = json.loads(path.read_text()) if path.exists() else {}
            yield data
            temp = path.with_suffix('.tmp')
            with temp.open('w') as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, path)

    def eligible(self, key, input_hash=None):
        with self.transaction() as data:
            row = data.get(key, {})
            status = row.get('status', 'queued')
            if status in self.TERMINAL:
                return status != 'rejected' and input_hash is not None and input_hash != row.get('input_hash')
            if status == 'running' and row.get('lease_until', 0) > self.clock():
                return False
            if row.get('input_hash') != input_hash:
                return True
            return row.get('attempts', 0) < self.max_attempts and row.get('retry_at', 0) <= self.clock()

    def block(self, key, reason, input_hash=None):
        with self.transaction() as data:
            old = data.get(key, {})
            if old.get('status') in self.TERMINAL or old.get('status') == 'running':
                return
            data[key] = {**old, 'status': 'blocked_inputs', 'reason': reason, 'input_hash': input_hash,
                         'retry_at': self.clock() + self.retry_seconds}

    def acquire(self, key, task_id, input_hash):
        with self.transaction() as data:
            old = data.get(key, {})
            if old.get('status') in self.TERMINAL and (old.get('status') == 'rejected' or old.get('input_hash') == input_hash):
                return None
            if old.get('status') == 'running' and old.get('lease_until', 0) > self.clock():
                return None
            changed = old.get('input_hash') != input_hash
            attempts = 0 if changed else old.get('attempts', 0)
            if attempts >= self.max_attempts or (not changed and old.get('retry_at', 0) > self.clock()):
                return None
            lease = uuid.uuid4().hex
            data[key] = {**old, 'task_id': task_id, 'status': 'running', 'lease': lease,
                         'lease_until': self.clock() + self.lease_seconds, 'input_hash': input_hash,
                         'attempts': attempts + 1, 'started': self.clock()}
            return lease

    def finish(self, key, lease, receipt):
        with self.transaction() as data:
            old = data.get(key, {})
            if old.get('lease') != lease or old.get('status') != 'running':
                return False
            status = receipt['status']
            data[key] = {**old, 'status': status, 'run_id': receipt.get('run_id'),
                         'finished': self.clock(), 'lease_until': 0,
                         'retry_at': self.clock() + self.retry_seconds * 2 ** max(0, old['attempts'] - 1),
                         'feedback': {'error': receipt.get('error'), 'review': receipt.get('review'),
                                      'validation': receipt.get('validation'), 'security_ok': receipt.get('security_ok')},
                         'receipt_path': receipt.get('receipt_path')}
            return True

    def feedback(self, key):
        with self.transaction() as data:
            return dict(data.get(key, {}).get('feedback') or {})

    def snapshot(self):
        with self.transaction() as data:
            return json.loads(json.dumps(data))
