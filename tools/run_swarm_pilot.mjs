// Explicit bounded launcher. Credentials remain in memory and child environment.
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { DatabaseSync } from 'node:sqlite';
import { homedir } from 'node:os';
import { dirname, resolve, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { mkdir, readFile, readdir, writeFile } from 'node:fs/promises';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const real = args.includes('--real');
const evolution = args.includes('--evolve');
const continuous = args.includes('--continuous');
const value = (name, fallback) => args.includes(name) ? args[args.indexOf(name)+1] : fallback;
const allowDb = args.includes('--use-omniroute-db-key');
const maxCalls = args.includes('--max-calls') ? Number(args[args.indexOf('--max-calls') + 1]) : 8;
if (!Number.isInteger(maxCalls) || maxCalls < 1 || maxCalls > 256) throw Error('max-calls must be 1..256');
const maxBatches = Number(value('--batches', '2'));
if (!Number.isInteger(maxBatches) || maxBatches < 1 || maxBatches > 8) throw Error('batches must be 1..8');
const state = resolve(value('--state-dir', resolve(root, 'scratch/selfopt', evolution ? 'stable-evolution' : real ? 'pilot-live' : 'pilot-offline')));
await mkdir(state, { recursive: true });
const env = { ...process.env, SELFOPT_NETWORK: real ? '1' : '0', SELFOPT_HERMES: real && evolution ? '1' : '0', SELFOPT_REQUEST_TIMEOUT: process.env.SELFOPT_REQUEST_TIMEOUT || '60' };
const options = ['selfopt_chain/orchestrator.py', '--state-dir', state, '--kill-switch', join(state, 'KILL_SWITCH'),
                 '--max-cycles', String(maxBatches), '--interval', '3', '--max-jobs', '1', '--max-calls', String(maxCalls), '--max-seconds', '300'];

if (real) {
  const gateway = new URL(env.SELFOPT_OMNIROUTE_URL || 'http://127.0.0.1:20128/v1');
  if (!['127.0.0.1','localhost','[::1]'].includes(gateway.hostname)) throw Error('Local gateway required');
  if (evolution) {
    if (!value('--quota-ledger', null)) throw Error('Evolution requires an explicit existing --quota-ledger; do not reset history');
    env.SELFOPT_HERMES_RUNTIME = resolve(value('--runtime', env.SELFOPT_HERMES_RUNTIME || ''));
    await readFile(join(env.SELFOPT_HERMES_RUNTIME,'READY.json'));
    env.SELFOPT_BASAL_URL = env.SELFOPT_BASAL_URL || 'http://127.0.0.1:8000';
    const basal = new URL(env.SELFOPT_BASAL_URL);
    if (!['127.0.0.1','localhost','[::1]'].includes(basal.hostname)) throw Error('Local basal required');
    const health = await fetch(env.SELFOPT_BASAL_URL+'/health',{signal:AbortSignal.timeout(5000)});
    if(!health.ok) throw Error('Local basal unavailable');
    options.push('--evolve-only','--evolve-max-tasks','1','--evolve-pause',value('--pause','60'),'--hermes-max-turns',value('--turns','12'),'--quota-ledger',resolve(value('--quota-ledger')));
    const timeAt=options.indexOf('--max-seconds'); options[timeAt+1]=value('--max-seconds','1800');
    if(continuous) options.splice(options.indexOf('--max-cycles'),2);
  }
  let key = env.SELFOPT_OMNIROUTE_KEY;
  let db;
  try {
    if (allowDb) db = new DatabaseSync(join(homedir(), '.omniroute/storage.sqlite'), { readOnly: true });
    if (!key && db) {
      const row = db.prepare("select key from api_keys where revoked_at is null and is_active=1 and (expires_at is null or expires_at>datetime('now')) order by case when lower(name) like '%selfopt%' then 0 else 1 end,created_at desc limit 1").get();
      if (!row?.key) throw Error('No active OmniRoute key');
      if (row.key.startsWith('enc:')) {
        const packageRoot = env.SELFOPT_OMNIROUTE_PACKAGE || resolve(dirname(process.execPath), '../lib/node_modules/omniroute');
        const chunks = join(packageRoot, 'dist/src/mitm');
        let decoder;
        for (const file of await readdir(chunks)) {
          if (!file.endsWith('.js')) continue;
          const source = await readFile(join(chunks, file), 'utf8');
          if (source.includes('function decrypt(ciphertext, opts)') && source.includes('init_encryption,')) {
            decoder = await import(pathToFileURL(join(chunks, file)).href); break;
          }
        }
        if (!decoder) throw Error('Installed OmniRoute decoder not found');
        decoder.init_encryption();
        key = decoder.decrypt(row.key, { quiet: true });
      } else key = row.key;
    }
    if (!key) throw Error('SELFOPT_OMNIROUTE_KEY required (database fallback needs explicit flag)');
    env.SELFOPT_OMNIROUTE_KEY = key;
    const base = env.SELFOPT_OMNIROUTE_URL || 'http://127.0.0.1:20128/v1';
    const response = await fetch(base + '/models', { headers: { Authorization: 'Bearer ' + key }, signal: AbortSignal.timeout(10000) });
    if (!response.ok) throw Error('Gateway catalog HTTP ' + response.status);
    const catalog = (await response.json()).data || [];
    // Only explicit :free model IDs. Provider names and aliases do not authorize use.
    const preference = ['cohere/north-mini-code:free', 'nvidia/nemotron-3.5-lightning:free', 'liquid/lfm-2.5-2.6b:free'];
    const candidates = preference.map(id => catalog.find(m => m.owned_by === 'kilocode' && m.id === 'kilocode/' + id)).filter(Boolean);
    if (candidates.length < 1) throw Error('No explicit supported :free model in authenticated catalog');
    const models = candidates.slice(0, 2).map(m => ({ model_id: m.id, provider: 'kilocode_free', role: 'bounded_pilot',
      quality_tier: 4, speed_class: 'fast', capabilities: ['text', 'json', 'code', 'reasoning'], privacy_class: 'public_only',
      cost_class: 'free_quota', context_tokens: 32768, rpm_seed: 8, rpd_seed: maxCalls, limits_verified: false,
      api: { style: 'openai_chat', base_url: base, secret_env: 'SELFOPT_OMNIROUTE_KEY', response_model_id: m.id.slice('kilocode/'.length) },
      notes: 'Explicit :free catalog ID; tier heuristic. Limits are conservative operator pilot caps; upstream quota unverified.' }));
    const registry = join(state, 'armed_registry.json');
    await writeFile(registry, JSON.stringify({ models }, null, 2));
    const snapshot = join(state, 'quota_snapshot.json');
    await writeFile(snapshot, JSON.stringify({ generated_at: new Date().toISOString(), entries: models.map(m => ({
      provider: m.provider, model: m.model_id, source: 'bounded_operator_pilot', checked_at: new Date().toISOString(),
      status: 'ok', rpm: 8, rpd: maxCalls, tpm: null, guaranteed: false, note: 'Operator cap only; upstream quota unverified' })) }, null, 2));
    options.push('--engine', 'omniroute', '--registry', registry, '--quota-snapshot', snapshot);
    console.log(JSON.stringify({ mode: 'real', state_dir: state, models: models.map(m => m.model_id), max_calls: maxCalls, upstream_quota_verified: false }));
  } finally { db?.close(); }
} else {
  options.push('--engine', 'mock', '--evolve', '--evolve-max-tasks', '2');
  console.log(JSON.stringify({ mode: 'offline', state_dir: state, max_calls: maxCalls }));
}
const sources = {};
for (const name of await readdir(join(root, 'selfopt_chain'))) {
  if (name.endsWith('.py')) sources[name] = createHash('sha256').update(await readFile(join(root, 'selfopt_chain', name))).digest('hex');
}
await writeFile(join(state, 'source_manifest_' + new Date().toISOString().replaceAll(':', '-') + '.json'), JSON.stringify({sources, started: new Date().toISOString(), max_calls: maxCalls}, null, 2));
const child = spawn('python3', options, { cwd: root, env, stdio: 'inherit' });
for (const signal of ['SIGTERM', 'SIGINT']) process.on(signal, () => child.kill(signal));
child.on('error', () => { console.error('Cannot start orchestrator'); process.exitCode = 1; });
child.on('exit', code => { process.exitCode = code ?? 1; });
