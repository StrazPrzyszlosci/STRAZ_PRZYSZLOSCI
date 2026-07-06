import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "straz-edge-installer" / "scripts" / "install-hermes-agent-proot.sh"
RUNBOOK = ROOT / "straz-edge-installer" / "scripts" / "RUNBOOK_HERMES_AGENT_PROOT.md"


class HermesProotInstallerTest(unittest.TestCase):
    def test_dry_run_requires_no_secrets_or_network(self):
        result = subprocess.run(["bash", str(SCRIPT), "--dry-run"], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("DRY_RUN_OK", result.stdout)
        self.assertIn("no packages installed", result.stdout)
        self.assertIn("no secrets written", result.stdout)

    def test_installer_defines_secret_hygiene_and_blocked_modes(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("hermes.env.example", text)
        self.assertIn("__SET_BY_OPERATOR__", text)
        self.assertIn("physical_actuation", text)
        self.assertIn("auto_merge", text)
        self.assertIn("direct_push_main", text)
        self.assertIn("quota_snapshot.json", text)

    def test_runbook_has_rollback_and_minimal_pat_guidance(self):
        text = RUNBOOK.read_text(encoding="utf-8")
        self.assertIn("Rollback", text)
        self.assertIn("GITHUB_PAT", text)
        self.assertIn("fork", text)
        self.assertIn("Nie commituj", text)
        self.assertIn("quota_snapshot.json", text)


if __name__ == "__main__":
    unittest.main()
