import json
from pathlib import Path

notebook_path = Path("/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/youtube-databaseparts.ipynb")

with open(notebook_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb["cells"]:
    if cell["cell_type"] == "code" and "# KOMÓRKA 3" in "".join(cell["source"]):
        source = "".join(cell["source"])
        
        # 1. Poprawka w verify_with_frame (aby zawsze zwracać słownik)
        old_verify_return = """            try:
                clean_text = response.text.replace('```json', '').replace('```', '').strip()
                return json.loads(clean_text), None"""
                
        new_verify_return = """            try:
                clean_text = response.text.replace('```json', '').replace('```', '').strip()
                data = json.loads(clean_text)
                if isinstance(data, list) and len(data) > 0:
                    data = data[0]
                return data, None"""

        # 2. Dodatkowe zabezpieczenie w pętli process_url
        old_ver_check = '                if ver and ver.get("verified") in [True, False]:'
        new_ver_check = '                if isinstance(ver, dict) and ver.get("verified") in [True, False]:'

        if old_verify_return in source:
            source = source.replace(old_verify_return, new_verify_return)
        if old_ver_check in source:
            source = source.replace(old_ver_check, new_ver_check)
            
        cell["source"] = [line + "\n" for line in source.split("\n")]
        if cell["source"][-1] == "\n": cell["source"].pop()
        elif cell["source"][-1].endswith("\n"): cell["source"][-1] = cell["source"][-1][:-1]

with open(notebook_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("Notebook updated with robust verification handling.")
