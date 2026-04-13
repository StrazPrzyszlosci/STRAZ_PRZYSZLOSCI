from __future__ import annotations

import shutil
import subprocess
import unittest


class CloudflareAiNodeSuite(unittest.TestCase):
    def test_node_suite(self) -> None:
        if shutil.which("node") is None:
            self.skipTest("Node.js nie jest dostępny w środowisku testowym.")

        result = subprocess.run(
            ["node", "--test", "cloudflare/tests/telegram_ai.test.mjs"],
            check=False,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            self.fail(
                "Node suite failed\nSTDOUT:\n"
                + result.stdout
                + "\nSTDERR:\n"
                + result.stderr
            )


if __name__ == "__main__":
    unittest.main()
