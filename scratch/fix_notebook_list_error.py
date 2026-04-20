import json
from pathlib import Path

notebook_path = Path("/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/youtube-databaseparts.ipynb")

with open(notebook_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb["cells"]:
    if cell["cell_type"] == "code" and "# KOMÓRKA 3" in "".join(cell["source"]):
        source = "".join(cell["source"])
        
        # Poprawka obsługi odpowiedzi AI (obsługa listy i słownika)
        old_logic = '            parts_to_verify = analysis.get("detected_parts", [])'
        new_logic = """            if isinstance(analysis, list):
                parts_to_verify = analysis
            elif isinstance(analysis, dict):
                parts_to_verify = analysis.get("detected_parts", [])
            else:
                parts_to_verify = []"""
        
        if old_logic in source:
            source = source.replace(old_logic, new_logic)
            
        cell["source"] = [line + "\n" for line in source.split("\n")]
        if cell["source"][-1] == "\n": cell["source"].pop()
        elif cell["source"][-1].endswith("\n"): cell["source"][-1] = cell["source"][-1][:-1]

with open(notebook_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("Notebook fixed: added robust handling for AI response (list vs dict).")
