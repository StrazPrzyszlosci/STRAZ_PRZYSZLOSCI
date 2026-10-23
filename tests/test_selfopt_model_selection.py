import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from selfopt_chain.model_selection import shortlist_models
from selfopt_chain.evolver import EvolutionLoop, EvolutionTask
from selfopt_chain.swarm import BasalDecisionCore
from selfopt_chain.omniroute import OmniRouteAdapter, FreeOnlyPolicy
from selfopt_chain.direct_patch_worker import DirectPatchWorker, PATCH_SCHEMA
from selfopt_chain.quota import QuotaLedger


def model(name, **changes):
    return {'model_id':name, 'cost_class':'free_quota', 'privacy_class':'public_only',
            'quality_tier':4, 'speed_class':'medium', 'capabilities':['text','code','json'],
            'context_tokens':32768, 'supports_tools':True, 'rpm_seed':10, 'rpd_seed':100, **changes}


class ModelSelectionTests(unittest.TestCase):
    def test_large_pool_is_ranked_before_basal_and_capped_at_twenty(self):
        pool = [model(f'm{i}') for i in range(316)]
        pool[-1]['quality_tier'] = 5
        result = shortlist_models(pool, kind='code_draft', hint='smart', limit=1000)
        self.assertEqual(len(result['candidates']),20)
        self.assertEqual(result['candidates'][0],'m315')
        self.assertEqual(result['eligible_count'],316)

    def test_role_tools_context_privacy_and_cost_are_hard_filters(self):
        pool = [model('good'), model('chat', supports_tools=False),
                model('moderation', routing_roles=['moderation']), model('short', context_tokens=512),
                model('private',privacy_class='local_private'),model('paid',cost_class='paid'),
                model('not-code',capabilities=['text'])]
        result = shortlist_models(pool,kind='code_draft',requires_tools=True,minimum_context_tokens=8192)
        self.assertEqual(result['candidates'],['good'])
        self.assertEqual(result['rejected']['chat'],'tools')
        self.assertEqual(result['rejected']['moderation'],'role')
        self.assertEqual(result['rejected']['short'],'context')
        self.assertEqual(result['rejected']['not-code'],'capabilities')

    def test_one_candidate_does_not_send_invalid_single_option_request(self):
        with tempfile.TemporaryDirectory() as tmp, patch('urllib.request.urlopen') as network:
            core = BasalDecisionCore()
            core.remote_url='http://127.0.0.1:8000'
            loop=EvolutionLoop(Path(tmp),Path(tmp),Path(tmp),models=[model('one')],lane_models=['one'],decision_core=core)
            self.assertEqual(loop._lane_model(0,EvolutionTask('t','work','test',kind='patch')),'one')
            network.assert_not_called()

    def test_missing_role_blocks_before_strategy_cost(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);models=[model('only-safety',routing_roles=['moderation'])]
            worker=Mock(models=models,ledger=QuotaLedger(models),executor_name='direct_patch')
            worker.enabled.return_value=True
            strategy=Mock()
            strategy.complete.side_effect=AssertionError('unqualified task spent a request')
            task=EvolutionTask('t','public proposal','test')
            with patch('selfopt_chain.evolver.collect_evolution_tasks',return_value=[task]):
                loop=EvolutionLoop(root,root,root,worker=worker,models=models,lane_models=['only-safety'],strategy_engine=strategy)
                self.assertEqual(loop.run(),[])
                self.assertEqual(loop.blocked[0]['kind'],'models')
                strategy.complete.assert_not_called()

    def test_structured_output_and_system_contract_reach_gateway(self):
        m=model('test:free')
        payload={'model':'test:free','choices':[{'message':{'content':'{"proposal":"x","edits":[],"new_files":[]}'}}]}
        task={'privacy':'public','system_prompt':'No tools. Return the supplied schema.',
              'response_format':{'type':'json_schema','json_schema':{'name':'patch','strict':True,'schema':PATCH_SCHEMA}},'max_tokens':8192}
        with patch.dict('os.environ',{'SELFOPT_NETWORK':'1'}), \
             patch('urllib.request.urlopen',return_value=io.BytesIO(json.dumps(payload).encode())) as request:
            result=OmniRouteAdapter(FreeOnlyPolicy([m])).complete(task,'public source','test:free')
        body=json.loads(request.call_args.args[0].data)
        self.assertTrue(result['ok'])
        self.assertEqual(body['messages'][0]['role'],'system')
        self.assertEqual(body['response_format'],task['response_format'])
        self.assertEqual(body['max_tokens'],8192)

    def test_foreign_tool_call_cannot_pass_as_a_patch_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'x.py').write_text('value = 1\n')
            worker=DirectPatchWorker([model('m')],QuotaLedger([model('m')]),root,root/'state')
            worker.engine=Mock()
            worker.engine.complete.return_value={'ok':True,'model_id':'m','output':json.dumps({'tool_name':'content','content':{'file_path':'x.py'}})}
            bundle={'kind':'patch','task_id':'t','title':'fix','allowed_paths':['x.py'],'input_files':{'x.py':'value = 1\n'}}
            with patch('selfopt_chain.direct_patch_worker.repository_snapshot',return_value=(root,'fixture')):
                receipt=worker.run_isolated('',model_alias='m',input_bundle=bundle)
            self.assertIn('invalid_producer_schema',receipt['error'])
            self.assertFalse(receipt['validation']['ok'])
            self.assertFalse((Path(receipt['quarantine_dir'])/'changes.patch').exists())


if __name__=='__main__':
    unittest.main()
