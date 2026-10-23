"""Read-only host capacity and process limits; no identifiers, secrets or probes."""
from __future__ import annotations

import os
import platform
import shutil
from datetime import datetime, timezone
from pathlib import Path


def _read(path):
    try:
        return path.read_text().strip()
    except (OSError, UnicodeError):
        return ''


def _integer(value):
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return None


def collect_hardware_context(workspace, *, proc_root=Path('/proc'), sys_root=Path('/sys')):
    """Capacity is observed on this controller; GPU presence is not backend readiness."""
    proc_root, sys_root = Path(proc_root), Path(sys_root)
    host_cpus = os.cpu_count()
    try:
        affinity = len(os.sched_getaffinity(0))
    except (AttributeError, OSError):
        affinity = host_cpus
    memory = {}
    for line in _read(proc_root / 'meminfo').splitlines():
        key, _, value = line.partition(':')
        if key in {'MemTotal', 'MemAvailable'}:
            parsed = _integer(value.split()[0]) if value.split() else None
            memory[key] = parsed * 1024 if parsed is not None else None
    model = next((line.partition(':')[2].strip() for line in _read(proc_root / 'cpuinfo').splitlines()
                  if line.startswith('model name')), None)

    # Include ancestors: the leaf can say "max" below a restricted user slice.
    cgroup_root = sys_root / 'fs/cgroup'
    roots = [cgroup_root]
    for line in _read(proc_root / 'self/cgroup').splitlines():
        if line.startswith('0::'):
            relative = Path(line[3:].lstrip('/'))
            if '..' not in relative.parts:
                leaf = cgroup_root / relative
                roots = [p for p in [leaf, *leaf.parents] if p == cgroup_root or cgroup_root in p.parents]
            break
    cpu_limits, memory_limits, memory_remaining = [], [], []
    for folder in roots[:32]:
        quota = _read(folder / 'cpu.max').split()
        if len(quota) == 2 and quota[0] != 'max':
            count, period = _integer(quota[0]), _integer(quota[1])
            if count is not None and period:
                cpu_limits.append(count / period)
        limit, used = _integer(_read(folder / 'memory.max')), _integer(_read(folder / 'memory.current'))
        if limit is not None:
            memory_limits.append(limit)
            if used is not None:
                memory_remaining.append(max(0, limit - used))
    effective_cpus = min([v for v in [affinity, *cpu_limits] if v is not None], default=None)
    total = min([v for v in [memory.get('MemTotal'), *memory_limits] if v is not None], default=None)
    available = min([v for v in [memory.get('MemAvailable'), *memory_remaining] if v is not None], default=None)
    if available is not None and total is not None:
        available = min(available, total)
    try:
        storage = shutil.disk_usage(workspace)
        disk = {'total_bytes': storage.total, 'free_bytes': storage.free}
    except OSError:
        disk = {'total_bytes': None, 'free_bytes': None}
    gpus = []
    for card in sorted((sys_root / 'class/drm').glob('card[0-9]*')):
        if not card.name[4:].isdigit():
            continue
        vendor = _read(card / 'device/vendor')
        if vendor:
            gpus.append({'vendor_id': vendor, 'device_id': _read(card / 'device/device'),
                         'vram_total_bytes': _integer(_read(card / 'device/mem_info_vram_total')),
                         'inference_backend_verified': False})
    return {'schema_version': 1, 'observed_at': datetime.now(timezone.utc).isoformat(),
            'scope': 'orchestrator_host', 'architecture': platform.machine(),
            'cpu': {'model': model, 'host_logical_cpus': host_cpus, 'affinity_cpus': affinity,
                    'quota_cores': min(cpu_limits, default=None), 'effective_cores': effective_cpus},
            'memory': {'host_total_bytes': memory.get('MemTotal'), 'host_available_bytes': memory.get('MemAvailable'),
                       'effective_total_bytes': total, 'effective_available_bytes': available},
            'workspace_storage': disk, 'gpus': gpus,
            'inference_policy': {'local': 'Basal decisions only', 'task_models': 'qualified free models through OmniRoute'},
            'hardware_model_constraint': 'Apply host capacity to local inference only; remote model size is not limited by host RAM or GPU.',
            'inventory_note': 'Resource offers and device profiles do not prove installed or available hardware.'}
