import sys
import os
import re

def split_sql(input_file, public_output, private_output):
    PUBLIC_TABLES = {
        'recycled_devices',
        'recycled_parts',
        'recycled_part_master',
        'recycled_device_parts',
        'recycled_part_aliases',
        'recycled_device_submissions',
        'schema_migrations',
        '_cf_KV'
    }

    PRIVATE_TABLES = {
        'telegram_chat_messages',
        'user_sessions'
    }

    TABLE_MATCH_PATTERN = re.compile(
        r'(?:CREATE\s+TABLE|INSERT\s+INTO|CREATE\s+INDEX|DROP\s+TABLE|'
        r'DELETE\s+FROM|ALTER\s+TABLE)\s+"?([a-zA-Z0-9_]+)"?',
        re.IGNORECASE
    )

    PRAGMA_PATTERN = re.compile(r'^\s*PRAGMA\s+', re.IGNORECASE)
    TRANSACTION_PATTERN = re.compile(r'^\s*(BEGIN|COMMIT|ROLLBACK)\s', re.IGNORECASE)

    public_lines = []
    private_lines = []

    current_table = None

    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            table_match = TABLE_MATCH_PATTERN.search(line)
            if table_match:
                current_table = table_match.group(1)

            transaction_match = TRANSACTION_PATTERN.match(line)
            pragma_match = PRAGMA_PATTERN.match(line)

            is_meta = bool(transaction_match or pragma_match)

            if is_meta or not current_table or (
                current_table not in PUBLIC_TABLES and
                current_table not in PRIVATE_TABLES
            ):
                public_lines.append(line)
                private_lines.append(line)
                continue

            if current_table in PUBLIC_TABLES:
                public_lines.append(line)
            elif current_table in PRIVATE_TABLES:
                private_lines.append(line)

    public_sql = "PRAGMA foreign_keys = OFF;\nBEGIN TRANSACTION;\n" + "".join(public_lines) + "COMMIT;\n"
    private_sql = "PRAGMA foreign_keys = OFF;\nBEGIN TRANSACTION;\n" + "".join(private_lines) + "COMMIT;\n"

    with open(public_output, 'w', encoding='utf-8') as f:
        f.write(public_sql)

    with open(private_output, 'w', encoding='utf-8') as f:
        f.write(private_sql)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python split_d1_backup.py <input.sql> <public.sql> <private.sql>")
        sys.exit(1)
    
    split_sql(sys.argv[1], sys.argv[2], sys.argv[3])
