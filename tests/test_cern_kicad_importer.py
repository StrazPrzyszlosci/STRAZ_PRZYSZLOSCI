import json
import tempfile
import unittest
from pathlib import Path

from pipelines.import_cern_kicad_library import (
    extract_top_level_symbol_forms,
    iter_components,
    normalize_part_number,
    parse_args,
    run_import,
)


SYMBOL_FIXTURE = '''
(kicad_symbol_lib (version 20240100) (generator "test")
  (symbol "TPS65994"
    (property "Reference" "U" (at 0 0 0))
    (property "Value" "TPS65994" (at 0 0 0))
    (property "Footprint" "Package_QFN:QFN-56-1EP_7x7mm_P0.4mm" (at 0 0 0))
    (property "Datasheet" "https://example.test/tps65994.pdf" (at 0 0 0))
    (property "MPN" "TPS65994AD" (at 0 0 0))
    (property "Manufacturer" "Texas Instruments" (at 0 0 0))
    (property "ki_keywords" "USB PD controller" (at 0 0 0))
    (symbol "TPS65994_0_1" (rectangle (start 0 0) (end 1 1)))
  )
)
'''

FOOTPRINT_FIXTURE = '''
(footprint "QFN-56-1EP_7x7mm_P0.4mm"
  (version 20240108)
  (generator "pcbnew")
  (descr "QFN fixture")
)
'''


class CernKicadImporterTests(unittest.TestCase):
    def test_normalize_part_number(self):
        self.assertEqual(normalize_part_number(" TPS-65994 AD "), "TPS65994AD")

    def test_extract_top_level_symbol_forms_skips_nested_symbols(self):
        forms = extract_top_level_symbol_forms(SYMBOL_FIXTURE)
        self.assertEqual(len(forms), 1)
        self.assertIn('(symbol "TPS65994"', forms[0])
        self.assertIn('TPS65994_0_1', forms[0])

    def test_iter_components_reads_symbol_and_footprint_fixture(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "CERN_Power.kicad_sym").write_text(SYMBOL_FIXTURE, encoding="utf-8")
            footprint_dir = root / "Package_QFN.pretty"
            footprint_dir.mkdir()
            (footprint_dir / "QFN-56-1EP_7x7mm_P0.4mm.kicad_mod").write_text(FOOTPRINT_FIXTURE, encoding="utf-8")

            rows = iter_components(root, {
                "source_slug": "cern-kicad-libs",
                "source_url": "https://gitlab.com/ohwr/cern-kicad-libs",
                "license_spdx": "CERN-OHL-P-2.0",
                "upstream_commit": "fixture",
                "kicad_version_family": "9.x",
            }, sample_limit=None)

        self.assertEqual(len(rows), 2)
        symbol = rows[0]
        self.assertEqual(symbol.symbol_name, "TPS65994")
        self.assertEqual(symbol.mpn, "TPS65994AD")
        self.assertEqual(symbol.normalized_part_number, "TPS65994AD")
        self.assertEqual(symbol.license_spdx, "CERN-OHL-P-2.0")
        footprint = rows[1]
        self.assertEqual(footprint.artifact_type, "footprint")
        self.assertEqual(footprint.footprint_name, "Package_QFN:QFN-56-1EP_7x7mm_P0.4mm")

    def test_run_import_writes_jsonl_csv_and_report(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source = temp_path / "source"
            output = temp_path / "out"
            source.mkdir()
            (source / "CERN_Power.kicad_sym").write_text(SYMBOL_FIXTURE, encoding="utf-8")

            args = parse_args([
                "--source", str(source),
                "--output-root", str(output),
                "--sample-limit", "10",
                "--upstream-commit", "fixture-commit",
                "--output-stamp", "TEST",
            ])
            result = run_import(args)

            self.assertEqual(result["count"], 1)
            jsonl_path = result["jsonl"]
            report_path = result["report"]
            self.assertTrue(jsonl_path.exists())
            self.assertTrue(result["csv"].exists())
            self.assertTrue(report_path.exists())
            row = json.loads(jsonl_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(row["upstream_commit"], "fixture-commit")
            self.assertEqual(row["symbol_name"], "TPS65994")
            report = report_path.read_text(encoding="utf-8")
            self.assertIn("Do not convert the full CERN KiCad library before ingest", report)


if __name__ == "__main__":
    unittest.main()
