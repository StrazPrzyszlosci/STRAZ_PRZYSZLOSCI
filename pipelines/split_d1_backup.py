import sys
import os
import re

def split_sql(input_file, public_output, private_output):
    # Tabele, które mają trafić do publicznego repozytorium (wiedza o częściach)
    PUBLIC_TABLES = {
        'recycled_devices',
        'recycled_parts',
        'recycled_part_master',
        'recycled_device_parts',
        'recycled_part_aliases',
        'recycled_device_submissions',
        'schema_migrations',
        '_cf_KV' # Metadane Cloudflare (opcjonalnie)
    }

    # Tabele, które mają trafić do prywatnego repozytorium (dane użytkowników i rozmów)
    PRIVATE_TABLES = {
        'telegram_chat_messages',
        'user_sessions'
    }

    public_lines = []
    private_lines = []
    
    current_table = None
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            # Szukamy początku definicji tabeli lub insertów
            # Format w D1 export: CREATE TABLE "name" ... lub INSERT INTO "name" ...
            table_match = re.search(r'(?:CREATE TABLE|INSERT INTO|CREATE INDEX|DROP TABLE|DELETE FROM) "?([a-zA-Z0-9_]+)"?', line)
            
            if table_match:
                current_table = table_match.group(1)
            
            # Jeśli linia nie pasuje do żadnej tabeli (np. komentarze, PRAGMA), 
            # dodajemy ją do obu plików dla zachowania struktury SQL
            if not current_table or (current_table not in PUBLIC_TABLES and current_table not in PRIVATE_TABLES):
                public_lines.append(line)
                private_lines.append(line)
                continue

            if current_table in PUBLIC_TABLES:
                public_lines.append(line)
            elif current_table in PRIVATE_TABLES:
                private_lines.append(line)

    with open(public_output, 'w', encoding='utf-8') as f:
        f.writelines(public_lines)
        
    with open(private_output, 'w', encoding='utf-8') as f:
        f.writelines(private_lines)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python split_d1_backup.py <input.sql> <public.sql> <private.sql>")
        sys.exit(1)
    
    split_sql(sys.argv[1], sys.argv[2], sys.argv[3])
