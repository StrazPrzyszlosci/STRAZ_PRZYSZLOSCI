import json
from pathlib import Path

notebook_path = Path("/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/youtube-databaseparts.ipynb")

with open(notebook_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb["cells"]:
    if cell["cell_type"] == "code" and "# KOMÓRKA 4" in "".join(cell["source"]):
        source = "".join(cell["source"])
        
        # Add -f flag to git add to ensure files are tracked
        old_add_1 = 'subprocess.run(["git", "-C", repo_dir, "add", file_1])'
        new_add_1 = 'subprocess.run(["git", "-C", repo_dir, "add", "-f", file_1])'
        
        old_add_2 = 'subprocess.run(["git", "-C", repo_dir, "add", file_2])'
        new_add_2 = 'subprocess.run(["git", "-C", repo_dir, "add", "-f", file_2])'
        
        source = source.replace(old_add_1, new_add_1).replace(old_add_2, new_add_2)
        
        cell["source"] = [line + "\n" for line in source.split("\n")]
        # cleanup last newline if split added extra
        if cell["source"][-1] == "\n": cell["source"].pop()
        elif cell["source"][-1].endswith("\n"): cell["source"][-1] = cell["source"][-1][:-1]

with open(notebook_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("Notebook updated with git add -f for database and history.")
