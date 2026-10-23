import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from selfopt_chain.evolution_publication import request_publication, record_published, stage_branch


class PublicationTests(unittest.TestCase):
    def prepare(self, root):
        queue, archive = root / 'evolution_queue/r', root / 'candidate_archive/f/r'
        queue.mkdir(parents=True)
        archive.mkdir(parents=True)
        patch = archive / 'changes.patch'
        patch.write_text('controlled patch bytes')
        receipt = {key: True for key in ['gate_ok', 'execution_ok', 'security_ok', 'validation_ok', 'review_ok']}
        receipt.update(title='fix failure', archive_path=str(archive), validation={'patch_sha256': hashlib.sha256(patch.read_bytes()).hexdigest()})
        path = queue / 'evolution_receipt.json'
        path.write_text(json.dumps(receipt))
        (queue / 'hermes_receipt.json').write_text(json.dumps({'source_commit': 'a' * 40}))
        return path, patch

    def test_ready_request_is_idempotent_and_records_real_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt, patch = self.prepare(root)
            request = request_publication(root, receipt, 'owner/repo')
            self.assertEqual(request_publication(root, receipt, 'owner/repo'), request)
            data = json.loads(request.read_text())
            self.assertFalse(data['auto_merge'])
            self.assertTrue(data['draft'])
            record_published(request, 'https://github.com/owner/repo/pull/12')
            self.assertEqual(json.loads(request.read_text())['status'], 'published')

    def test_tampering_or_unready_receipt_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt, patch = self.prepare(root)
            patch.write_text('tampered')
            with self.assertRaisesRegex(ValueError, 'patch_changed'):
                request_publication(root, receipt, 'owner/repo')
            data = json.loads(receipt.read_text());data['validation_ok'] = False;receipt.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'candidate_not_ready'):
                request_publication(root, receipt, 'owner/repo')

    def test_main_branch_can_never_be_staged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt, _ = self.prepare(root)
            request = request_publication(root, receipt, 'owner/repo')
            data = json.loads(request.read_text());data['branch'] = 'main';request.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'publication_policy'):
                stage_branch(request, root)
