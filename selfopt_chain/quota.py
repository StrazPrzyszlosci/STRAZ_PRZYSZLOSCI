"""Atomic per-model attempts, rolling RPM and daily limits shared by all lanes."""
from __future__ import annotations

import fcntl
import json
import os
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


class QuotaExceeded(RuntimeError):
    pass


class QuotaLedger:
    def __init__(self, models, path: Path | None = None, *, max_calls=None, clock=time.time, should_stop=None, seed_daily=None):
        self.limits = {m['model_id']: (m.get('rpm_seed', 0), m.get('rpd_seed', 0)) for m in models}
        self.pools = {m['model_id']: m.get('quota_pool', m.get('provider', m['model_id'])) for m in models}
        self.pool_limits = {}
        for mid, pool in self.pools.items():
            limits = self.limits[mid]
            self.pool_limits[pool] = tuple(min(a, b) for a, b in zip(self.pool_limits.get(pool, limits), limits))
        self.path = Path(path) if path else None
        self.max_calls = max_calls
        self.clock = clock
        self.should_stop = should_stop or (lambda: False)
        self.lock = threading.RLock()
        self.data = {}
        self.seed_daily = dict(seed_daily or {})

    @contextmanager
    def transaction(self):
        with self.lock:
            handle = None
            try:
                if self.path:
                    self.path.parent.mkdir(parents=True, exist_ok=True)
                    handle = self.path.with_suffix('.lock').open('a+')
                    fcntl.flock(handle, fcntl.LOCK_EX)
                    self.data = json.loads(self.path.read_text()) if self.path.exists() else {}
                now = self.clock()
                day = datetime.fromtimestamp(now, timezone.utc).date().isoformat()
                if self.data.get('date') != day:
                    self.data = {'date': day, 'daily': self.seed_daily, 'minute': {}}
                    self.seed_daily = {}
                self.data['minute'] = {m: [t for t in times if now - t < 60] for m, times in self.data['minute'].items()}
                yield self.data
                if self.path:
                    temp = self.path.with_suffix('.tmp')
                    temp.write_text(json.dumps(self.data, indent=2) + '\n')
                    os.replace(temp, self.path)
            finally:
                if handle:
                    handle.close()

    def _availability(self, data, model_id):
        if self.should_stop():
            return {'allowed': False, 'reason': 'stopped'}
        if model_id not in self.limits:
            return {'allowed': False, 'reason': 'unknown_model'}
        rpm, rpd = self.limits.get(model_id, (0, 0))
        pool = self.pools.get(model_id)
        peers = [mid for mid, group in self.pools.items() if group == pool]
        pool_rpm, pool_rpd = self.pool_limits.get(pool, (0, 0))
        if self.max_calls is not None and sum(data['daily'].values()) >= self.max_calls:
            return {'allowed': False, 'reason': 'global_daily_limit'}
        if data['daily'].get(model_id, 0) >= rpd or sum(data['daily'].get(mid, 0) for mid in peers) >= pool_rpd:
            return {'allowed': False, 'reason': 'daily_limit'}
        retry = data.get('health', {}).get(model_id, {}).get('cooldown_until', 0) - self.clock()
        if retry > 0:
            return {'allowed': False, 'reason': 'provider_cooldown', 'retry_after_s': retry}
        if len(data['minute'].get(model_id, [])) >= rpm or sum(len(data['minute'].get(mid, [])) for mid in peers) >= pool_rpm:
            return {'allowed': False, 'reason': 'minute_limit'}
        return {'allowed': True, 'reason': 'ready'}

    def _allowed(self, data, model_id):
        return self._availability(data, model_id)['allowed']

    def availability(self, model_id):
        with self.transaction() as data:
            return self._availability(data, model_id)

    def can_use(self, model_id):
        with self.transaction() as data:
            return self._allowed(data, model_id)

    def record(self, model_id):
        with self.transaction() as data:
            if not self._allowed(data, model_id):
                raise QuotaExceeded('quota_exhausted_or_stopped')
            data['daily'][model_id] = data['daily'].get(model_id, 0) + 1
            data['minute'].setdefault(model_id, []).append(self.clock())

    def record_outcome(self, model_id, result):
        with self.transaction() as data:
            row = data.setdefault('health', {}).setdefault(model_id, {'successes': 0, 'failures': 0})
            if result.get('ok'):
                row['successes'] += 1
                row['consecutive_failures'] = 0
                row['cooldown_until'] = 0
            else:
                row['failures'] += 1
                if result.get('error_class') in {'connection_error', 'http_error', 'bad_response'}:
                    row['consecutive_failures'] = row.get('consecutive_failures', 0) + 1
                    row['cooldown_until'] = self.clock() + min(900, 120 * 2 ** (row['consecutive_failures'] - 1))
            row['last_error_class'] = result.get('error_class')
            row['last_latency_ms'] = result.get('latency_ms')

    def model_observations(self, model_id):
        with self.transaction() as data:
            row = data.get('health', {}).get(model_id, {})
            return {key: row.get(key) for key in
                    ['successes', 'failures', 'consecutive_failures', 'last_error_class', 'last_latency_ms']}

    @property
    def rpd_used(self):
        with self.transaction() as data:
            return dict(data['daily'])

    @property
    def rpm_used(self):
        with self.transaction() as data:
            return {m: len(times) for m, times in data['minute'].items()}

    def rpd_headroom(self, model_id):
        return self.limits.get(model_id, (0, 0))[1] - self.rpd_used.get(model_id, 0)

    def _remaining_pools(self, data):
        pools = {pool: max(0, limits[1] - sum(data['daily'].get(mid, 0)
                 for mid, group in self.pools.items() if group == pool))
                 for pool, limits in self.pool_limits.items()}
        remaining = sum(pools.values())
        if self.max_calls is not None:
            remaining = min(remaining, max(0, self.max_calls - sum(data['daily'].values())))
        # Rezerwacje procesów (holderzy) odejmowane od każdego admissionu,
        # także współbieżnych — record() nadal egzekwuje per-model.
        remaining -= sum(data.get('reserved', {}).values())
        return max(0, remaining), pools

    def reserve(self, holder: str, n: int) -> bool:
        """Atomowe objęcie n wywołań na cały proces (strategia+producent+review).

        True = hold przyznany i widoczny dla pozostałych admissionów; release()
        zdejmuje hold po zakończeniu procesu. Nie zwalnia per-model limitów.
        """
        with self.transaction() as data:
            remaining, _ = self._remaining_pools(data)
            if n > remaining:
                return False
            reserved = data.setdefault('reserved', {})
            reserved[holder] = reserved.get(holder, 0) + n
            return True

    def release(self, holder: str) -> None:
        with self.transaction() as data:
            data.get('reserved', {}).pop(holder, None)

    def remaining_daily_calls(self, model_id=None):
        """Admission estimate, including shared pools, reservations and the optional cap.

        This is a snapshot; record() still enforces every attempt, and reserve()
        holds budget atomically for the duration of a whole process.
        """
        with self.transaction() as data:
            remaining, pools = self._remaining_pools(data)
            if model_id is not None:
                if model_id not in self.limits:
                    return 0
                remaining = min(remaining, pools[self.pools[model_id]],
                                max(0, self.limits[model_id][1] - data['daily'].get(model_id, 0)))
            return remaining


class BudgetedEngine:
    """Strategy, review and nodes use the same model policy and accounting."""
    def __init__(self, engine, models, ledger, should_stop=None, decision_core=None):
        self.engine, self.models, self.ledger = engine, models, ledger
        self.should_stop = should_stop or (lambda: False)
        self.decision_core = decision_core

    def complete(self, task, model_id, prompt):
        from selfopt_chain.router import route_task
        if self.should_stop():
            return {'ok': False, 'output': '', 'error_class': 'stopped'}
        if task.get('privacy') != 'public':
            return {'ok': False, 'output': '', 'error_class': 'privacy_violation'}
        # Aliases are resolved locally, before any provider request or reservation.
        eligible = [m for m in self.models if not model_id.startswith('auto') or m.get('privacy_class') != 'local_private']
        if model_id.startswith('auto'):
            decision = route_task(task, eligible, self.ledger)
            model_id = (decision.get('chosen') or {}).get('model_id', '')
            if model_id and self.decision_core is not None:
                from selfopt_chain.model_selection import shortlist_models
                selection = shortlist_models(eligible, kind=task.get('kind', ''), ledger=self.ledger,
                    requires=task.get('requires', []) or [],
                    minimum_context_tokens=len(prompt.encode()) // 2 + int(task.get('max_tokens', 4096)))
                # T60: basal dostaje TYLKO wykonalne opcje — modele w cooldown,
                # minute-limit lub daily-limit nie wchodzą na listę.
                options = [o for o in selection['candidates'] if self.ledger.can_use(o)]
                if not options:
                    return {'ok': False, 'output': '', 'error_class': 'no_eligible_model'}
                default = model_id if model_id in options else options[0]
                chosen = self.decision_core.decide('model_selection', options, selection['scores'],
                    default_option=default, context={'task_id': task.get('task_id'),
                        'kind': task.get('kind'), 'model_characteristics': selection['details']})
                model_id = chosen['final'] if chosen.get('final') in options else default
        elif not any(m['model_id'] == model_id for m in eligible):
            model_id = ''
        # T60: jawna przyczyna odmowy (provider_cooldown/minute_limit/daily_limit)
        # zamiast uogólnionego quota_exhausted — przed rezerwacją.
        availability = self.ledger.availability(model_id)
        if not availability.get('allowed'):
            return {'ok': False, 'output': '', 'error_class': availability.get('reason', 'unavailable'),
                    'error_origin': 'local', 'requested_model_id': model_id}
        try:
            self.ledger.record(model_id)
        except QuotaExceeded:
            return {'ok': False, 'output': '', 'error_class': 'quota_exhausted', 'error_origin': 'local'}
        result = self.engine.complete(task, model_id, prompt)
        # T60/cold-start (dyrektywa operatora 2026-10-24): NIM zawsze wolno
        # startuje model za PIERWSZYM razem — pierwsza sonda modelu bez żadnego
        # sukcesu to ładowanie, nie porażka jakości. Nie wywala cooldownu;
        # natychmiastowa ponowa na rozgrzanym modelzie (rozliczona w ledgerze).
        observations = self.ledger.model_observations(model_id)
        cold_start = (not result.get('ok')
                      and result.get('error_class') in {'connection_error', 'http_error', 'bad_response'}
                      and observations.get('successes', 0) == 0)
        if result.get('ok') or not cold_start:
            self.ledger.record_outcome(model_id, result)
        else:
            self.ledger.record_outcome(model_id, {**result, 'error_class': 'cold_start_probe'})
            if not self.should_stop() and self.ledger.can_use(model_id):
                try:
                    self.ledger.record(model_id)
                    retry = self.engine.complete(task, model_id, prompt)
                    self.ledger.record_outcome(model_id, retry)
                    retry['cold_start_retried'] = True
                    result = retry
                except QuotaExceeded:
                    pass
        result["attempt_recorded"] = True
        result["requested_model_id"] = model_id
        return result
