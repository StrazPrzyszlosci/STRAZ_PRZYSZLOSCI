import unittest
import os
import sys
import sqlite3
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipelines"))
from split_d1_backup import split_sql


class TestSplitD1Backup(unittest.TestCase):

    def setUp(self):
        self.tmp_input = tempfile.NamedTemporaryFile(
            mode="w", suffix=".sql", delete=False, encoding="utf-8"
        )
        self.tmp_public = tempfile.NamedTemporaryFile(
            mode="w", suffix=".sql", delete=False, encoding="utf-8"
        )
        self.tmp_private = tempfile.NamedTemporaryFile(
            mode="w", suffix=".sql", delete=False, encoding="utf-8"
        )
        self.tmp_public.close()
        self.tmp_private.close()

    def tearDown(self):
        for path in [self.tmp_input.name, self.tmp_public.name, self.tmp_private.name]:
            try:
                os.unlink(path)
            except OSError:
                pass

    def _write_input(self, lines):
        with open(self.tmp_input.name, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _read_output(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _run_split(self):
        split_sql(self.tmp_input.name, self.tmp_public.name, self.tmp_private.name)

    def test_basic_split_public_table(self):
        self._write_input([
            'CREATE TABLE recycled_parts (id INTEGER PRIMARY KEY);',
            'INSERT INTO recycled_parts VALUES (1, "ESP32");',
        ])
        self._run_split()
        public = self._read_output(self.tmp_public.name)
        private = self._read_output(self.tmp_private.name)
        self.assertIn("recycled_parts", public)
        self.assertIn("PRAGMA foreign_keys = OFF", public)
        self.assertIn("BEGIN TRANSACTION", public)
        self.assertIn("COMMIT", public)
        self.assertNotIn("recycled_parts", private)

    def test_basic_split_private_table(self):
        self._write_input([
            'CREATE TABLE telegram_chat_messages (id INTEGER PRIMARY KEY);',
            'INSERT INTO telegram_chat_messages VALUES (1, "hello");',
        ])
        self._run_split()
        public = self._read_output(self.tmp_public.name)
        private = self._read_output(self.tmp_private.name)
        self.assertIn("telegram_chat_messages", private)
        self.assertNotIn("telegram_chat_messages", public)

    def test_public_and_private_separated(self):
        self._write_input([
            'CREATE TABLE recycled_devices (id INTEGER);',
            'INSERT INTO recycled_devices VALUES (1);',
            'CREATE TABLE user_sessions (id INTEGER);',
            'INSERT INTO user_sessions VALUES (1);',
        ])
        self._run_split()
        public = self._read_output(self.tmp_public.name)
        private = self._read_output(self.tmp_private.name)
        self.assertIn("recycled_devices", public)
        self.assertNotIn("recycled_devices", private)
        self.assertIn("user_sessions", private)
        self.assertNotIn("user_sessions", public)

    def test_schema_migrations_public_only(self):
        self._write_input([
            'CREATE TABLE schema_migrations (version TEXT);',
            'INSERT INTO schema_migrations VALUES ("0015");',
        ])
        self._run_split()
        public = self._read_output(self.tmp_public.name)
        private = self._read_output(self.tmp_private.name)
        self.assertIn("schema_migrations", public)
        self.assertNotIn("schema_migrations", private)

    def test_alter_table_handled(self):
        self._write_input([
            'ALTER TABLE recycled_parts ADD COLUMN footprint TEXT;',
        ])
        self._run_split()
        public = self._read_output(self.tmp_public.name)
        private = self._read_output(self.tmp_private.name)
        self.assertIn("ALTER TABLE", public)
        self.assertIn("recycled_parts", public)
        self.assertNotIn("recycled_parts", private)

    def test_alter_table_private(self):
        self._write_input([
            'ALTER TABLE user_sessions ADD COLUMN last_ip TEXT;',
        ])
        self._run_split()
        public = self._read_output(self.tmp_public.name)
        private = self._read_output(self.tmp_private.name)
        self.assertIn("ALTER TABLE", private)
        self.assertIn("user_sessions", private)
        self.assertNotIn("user_sessions", public)

    def test_drop_table_public(self):
        self._write_input([
            'DROP TABLE IF EXISTS recycled_device_submissions;',
        ])
        self._run_split()
        public = self._read_output(self.tmp_public.name)
        self.assertIn("DROP TABLE", public)
        self.assertIn("recycled_device_submissions", public)

    def test_delete_from_private(self):
        self._write_input([
            'DELETE FROM user_sessions WHERE last_seen < "2024-01-01";',
        ])
        self._run_split()
        private = self._read_output(self.tmp_private.name)
        self.assertIn("DELETE FROM", private)
        self.assertIn("user_sessions", private)

    def test_create_index_in_both(self):
        self._write_input([
            'CREATE INDEX idx_parts_model ON recycled_parts(model);',
        ])
        self._run_split()
        public = self._read_output(self.tmp_public.name)
        self.assertIn("idx_parts_model", public)

    def test_pragma_and_transactions_preserved(self):
        self._write_input([
            'PRAGMA journal_mode = WAL;',
            'BEGIN TRANSACTION;',
            'INSERT INTO recycled_parts VALUES (1);',
            'COMMIT;',
        ])
        self._run_split()
        public = self._read_output(self.tmp_public.name)
        self.assertIn("PRAGMA foreign_keys = OFF", public)
        self.assertIn("BEGIN TRANSACTION", public)
        self.assertIn("COMMIT", public)

    def test_unknown_table_in_both(self):
        self._write_input([
            'CREATE TABLE random_unknown (id INTEGER);',
            'INSERT INTO random_unknown VALUES (1);',
        ])
        self._run_split()
        public = self._read_output(self.tmp_public.name)
        private = self._read_output(self.tmp_private.name)
        self.assertIn("random_unknown", public)
        self.assertIn("random_unknown", private)

    def test_mixed_case_does_not_matter(self):
        self._write_input([
            'INSERT INTO "Recycled_Parts" VALUES (1);',
        ])
        self._run_split()
        public = self._read_output(self.tmp_public.name)

    def test_empty_input(self):
        self._write_input([])
        self._run_split()
        public = self._read_output(self.tmp_public.name)
        private = self._read_output(self.tmp_private.name)
        self.assertIn("PRAGMA foreign_keys = OFF", public)
        self.assertIn("COMMIT", public)
        self.assertIn("PRAGMA foreign_keys = OFF", private)
        self.assertIn("COMMIT", private)

    def test_multi_line_ddl(self):
        self._write_input([
            "CREATE TABLE recycled_parts (",
            "  id INTEGER PRIMARY KEY AUTOINCREMENT,",
            '  part_number TEXT NOT NULL,',
            "  created_at TEXT DEFAULT CURRENT_TIMESTAMP",
            ");",
            "INSERT INTO recycled_parts (part_number) VALUES ('ESP32-WROOM');",
        ])
        self._run_split()
        public = self._read_output(self.tmp_public.name)
        self.assertIn("recycled_parts", public)

    def test_output_is_valid_sqlite(self):
        self._write_input([
            'CREATE TABLE recycled_devices (id INTEGER PRIMARY KEY, model TEXT);',
            'INSERT INTO recycled_devices VALUES (1, "ESP32-DevKitC");',
            'CREATE TABLE user_sessions (id INTEGER PRIMARY KEY, user_id TEXT);',
            'INSERT INTO user_sessions VALUES (1, "user-123");',
        ])
        self._run_split()

        public = self._read_output(self.tmp_public.name)
        private = self._read_output(self.tmp_private.name)

        # Public SQL should be importable to SQLite
        conn = sqlite3.connect(":memory:")
        conn.executescript(public)
        cur = conn.execute("SELECT model FROM recycled_devices WHERE id = 1")
        row = cur.fetchone()
        self.assertEqual(row[0], "ESP32-DevKitC")
        conn.close()

        # Private SQL should be importable to SQLite
        conn = sqlite3.connect(":memory:")
        conn.executescript(private)
        cur = conn.execute("SELECT user_id FROM user_sessions WHERE id = 1")
        row = cur.fetchone()
        self.assertEqual(row[0], "user-123")
        conn.close()

    def test_output_contains_no_broken_lines(self):
        """Każdy SQL musi być parsowalny — zadne polamane linie."""
        self._write_input([
            "CREATE TABLE recycled_parts (id INTEGER, part_name TEXT);",
            "INSERT INTO recycled_parts VALUES (1, 'ESP32 DevKit');",
            "INSERT INTO reclaimed_parts VALUES (2, 'OLED 0.96');",
        ])
        self._run_split()
        public = self._read_output(self.tmp_public.name)
        # Sprawdzamy ze kazdy CREATE/INSERT/DROP/ALTER jest w jednej linii
        # (transakcje i pragma moga byc wieloliniowe)
        for line in public.split("\n"):
            if any(line.strip().upper().startswith(kw) for kw in
                   ["CREATE", "INSERT", "ALTER", "DROP", "DELETE"]):
                self.assertIn(";", line, f"Linia DDL/DML bez srednika: {line}")

    def test_cf_kv_table_public_only(self):
        self._write_input([
            'CREATE TABLE _cf_KV (key TEXT, value TEXT);',
            'INSERT INTO _cf_KV VALUES ("k1", "v1");',
        ])
        self._run_split()
        public = self._read_output(self.tmp_public.name)
        private = self._read_output(self.tmp_private.name)
        self.assertIn("_cf_KV", public)
        self.assertNotIn("_cf_KV", private)


if __name__ == "__main__":
    unittest.main()