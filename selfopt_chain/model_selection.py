"""Role and resource filters precede the small local decision model."""
from __future__ import annotations

MAX_BASAL_OPTIONS = 20


def shortlist_models(models, *, kind, ledger=None, hint='', requires_tools=False,
                     minimum_context_tokens=0, requires=(), limit=8):
    if limit < 1:
        raise ValueError('shortlist limit must be positive')
    limit = min(limit, MAX_BASAL_OPTIONS)
    from selfopt_chain.router import required_tier_for_kind
    required = ({'text', 'code', 'json'} if kind == 'code_draft' else {'text'}) | set(requires)
    minimum_tier = required_tier_for_kind(kind)
    candidates, rejected, scores, details = [], {}, {}, {}
    for order, model in enumerate(models):
        mid = model['model_id']
        reason = None
        if model.get('cost_class') != 'free_quota' or model.get('privacy_class') != 'public_only':
            reason = 'cost_or_privacy'
        elif kind not in model.get('routing_roles', [kind]):
            reason = 'role'
        elif not required.issubset(model.get('capabilities', [])):
            reason = 'capabilities'
        elif model.get('quality_tier', 0) < minimum_tier:
            reason = 'tier'
        elif model.get('context_tokens', 0) < minimum_context_tokens:
            reason = 'context'
        elif requires_tools and model.get('supports_tools') is not True:
            reason = 'tools'
        elif ledger is not None and not ledger.can_use(mid):
            reason = 'resource_unavailable'
        if reason:
            rejected[mid] = reason
            continue
        speed = {'fast': 1.0, 'medium': 0.6, 'slow': 0.2}.get(model.get('speed_class'), 0.5)
        quality = model['quality_tier'] / 5
        score = 2 * quality + speed / 4 if hint == 'smart' else speed + quality / 2
        evidence = {'quality_tier': model['quality_tier'], 'speed_class': model.get('speed_class'),
                    'capabilities': model['capabilities'], 'routing_roles': model.get('routing_roles'),
                    'supports_tools': model.get('supports_tools'), 'execution_location': 'remote_api',
                    'host_hardware_limits_model_size': False}
        if ledger is not None and hasattr(ledger, 'model_observations'):
            observed = ledger.model_observations(mid)
            good, bad = observed.get('successes') or 0, observed.get('failures') or 0
            score *= 0.5 + (good + 1) / (good + bad + 2)
            evidence['observed_transport'] = observed
        scores[mid], details[mid] = score, evidence
        candidates.append((score, order, mid))
    candidates.sort(key=lambda row: (-row[0], row[1]))
    selected = [mid for _, _, mid in candidates[:limit]]
    return {'candidates': selected, 'scores': {mid: scores[mid] for mid in selected},
            'details': {mid: details[mid] for mid in selected}, 'rejected': rejected,
            'eligible_count': len(candidates), 'limit': limit}
