import difflib
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from selfopt_chain.evolution_validation import validate_patch
from selfopt_chain.evolution_inputs import prepare_inputs
from selfopt_chain.evolver import EvolutionLoop, EvolutionTask

ROOT = Path(__file__).resolve().parents[1]


class ValidatorBoundaryTests(unittest.TestCase):
    def test_patch_paths_do_not_inherit_parent_git_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(['git','init','-q',str(root)],check=True)
            snapshot = root / 'nested/snapshot';snapshot.mkdir(parents=True)
            output = root / 'output';output.mkdir()
            old,new='value = 1\n','value = 2\n'
            (snapshot/'sample.py').write_text(old)
            (output/'PROPOSAL.md').write_text('Fix value')
            (output/'changes.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/sample.py',tofile='b/sample.py')))
            def command(sandbox,*args,**kwargs):
                return [sys.executable,'-c','raise SystemExit('+('1' if sandbox.workspace==snapshot.resolve() else '0')+')']
            with patch('selfopt_chain.evolution_validation.Sandbox.command',command), \
                 patch('selfopt_chain.evolution_validation.Sandbox.run',return_value=subprocess.CompletedProcess([],0,'','')):
                report=validate_patch(output,snapshot,{'allowed_paths':['sample.py'],'acceptance':'controlled'},root/'validation')
            self.assertEqual(report['changed_paths'],['sample.py'])
            self.assertNotEqual(report.get('error'),'patch_outside_scope')

    def test_revalidation_preserves_original_model_code_and_counts_no_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            state=Path(tmp)
            task=EvolutionTask('task','fix defer','test',kind='patch',allowed_paths=['sample.py'],acceptance_ref='selfopt_chain/evolution_acceptance/deferred_selection.py')
            manifest=prepare_inputs(task,ROOT,state)
            output=state/'direct_quarantine/original';output.mkdir(parents=True)
            (output/'changes.patch').write_text('original model patch')
            (output/'PROPOSAL.md').write_text('original model proposal')
            before=(output/'changes.patch').read_bytes()
            queue=state/'evolution_queue/original';queue.mkdir(parents=True)
            fp=EvolutionLoop.fingerprint(task)
            old={'task_id':'task','run_id':'original','title':task.title,'source':'test','executor':'direct_patch','fingerprint':fp,'input_hash':manifest['input_hash'],
                 'execution_ok':True,'security_ok':True,'validation_ok':False,'review':{'verdict':'unreviewed'},'proposal_path':str(output/'PROPOSAL.md')}
            receipt=queue/'evolution_receipt.json';receipt.write_text(json.dumps(old))
            (queue/'hermes_receipt.json').write_text(json.dumps({'quarantine_dir':str(output),'source_commit':'a'*40,'api_calls':{'model':1}}))
            class Review:
                def complete(self,*args):return {'ok':True,'model_id':'review','output':'{"verdict":"pass","notes":"complete"}'}
            loop=EvolutionLoop(state,ROOT/'docs',ROOT,strategy_engine=Review())
            validation={'ok':True,'checks':{},'patch_sha256':hashlib.sha256(before).hexdigest()}
            with patch('selfopt_chain.evolver.collect_evolution_tasks',return_value=[task]), \
                 patch('selfopt_chain.evolution_validation.validate_patch',return_value=validation):
                result=loop.revalidate(receipt)
            self.assertEqual(result['status'],'ready')
            self.assertFalse(result['producer_rerun'])
            self.assertEqual((output/'changes.patch').read_bytes(),before)
            produced=json.loads((Path(result['receipt_path']).parent/'hermes_receipt.json').read_text())
            self.assertEqual(produced['api_calls'],{})
            self.assertEqual(produced['original_api_calls'],{'model':1})
