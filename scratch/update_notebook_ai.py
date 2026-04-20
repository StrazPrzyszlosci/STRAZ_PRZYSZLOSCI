import json
from pathlib import Path

notebook_path = Path("/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/youtube-databaseparts.ipynb")

with open(notebook_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb["cells"]:
    if cell["cell_type"] == "code" and "# KOMÓRKA 3" in "".join(cell["source"]):
        source = "".join(cell["source"])
        
        # 1. Expand YTPartsExtractor to include enrichment logic
        # We will add a prompt for Gemini to also identify footprint and datasheet search query
        old_prompt_v1 = """            prompt = (
                f"Spójrz na tę klatkę w wysokiej rozdzielczości wyciągniętą z filmu o naprawie elektroniki. "
                f"Twoim jedynym zadaniem jest dokładne odczytanie numerów seryjnych, oznaczeń modeli (np. układów KBC, chipów, modułów) "
                f"lub kodów kreskowych z elementu ukazanego w kadrze.\\n"
                f"Model fazy 1 zasugerował: '{expected_part_number}'. Jeśli to 'REQUIRES_HQ_CHECK', zignoruj tę podpowiedź i po prostu odczytaj to co widzisz.\\n"
                f"Odpowiedz TYLKO i WYŁĄCZNIE w formacie JSON:\\n"
                f"{{\\\"verified\\\": true/false, \\\"observed_text\\\": \\\"DOKŁADNY_ODCZYTANY_NUMER_LUB_BRAK\\\"}}"
            )"""
            
        new_prompt_v1 = """            prompt = (
                f"Spójrz na tę klatkę w wysokiej rozdzielczości z filmu o naprawie elektroniki. "
                f"1. Dokładnie odczytaj numer seryjny/model układu (np. KBC, chip, kontroler). "
                f"2. Zidentyfikuj typ obudowy (footprint, np. SOT-23, SOIC-8, QFN, BGA). "
                f"3. Podaj krótki opis pinoutu jeśli to możliwe (np. gdzie jest pin 1). "
                f"Model fazy 1 zasugerował: '{expected_part_number}'.\\n"
                f"Odpowiedz TYLKO i WYŁĄCZNIE w formacie JSON:\\n"
                f"{{\\\"verified\\\": true, \\\"observed_text\\\": \\\"NUMER\\\", \\\"footprint\\\": \\\"TYP\\\", \\\"pinout\\\": {{\\\"summary\\\": \\\"OPIS\\\"}}, \\\"datasheet_search_query\\\": \\\"NUMER datasheet pdf\\\"}}"
            )"""

        if old_prompt_v1 in source:
            source = source.replace(old_prompt_v1, new_prompt_v1)

        # 2. Update save_result to record expanded fields
        old_record = """                record = {
                    "timestamp_db": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "device": device, "part_name": part.get("part_name"),
                    "part_number": part_number_val, "confidence": part.get("confidence", 0.0),
                    "yt_link": part.get("yt_link_with_time"),
                    "verification": part.get("verification", {}), "source_video": url
                }"""
        
        new_record = """                v_info = part.get("verification", {})
                record = {
                    "timestamp_db": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "device": device,
                    "part_name": part.get("part_name"),
                    "part_number": part_number_val,
                    "footprint": v_info.get("footprint", "Unknown"),
                    "datasheet_url": f"https://www.google.com/search?q={v_info.get('datasheet_search_query', part_number_val + ' datasheet pdf')}",
                    "pinout": v_info.get("pinout", {}),
                    "confidence": part.get("confidence", 0.0),
                    "yt_link": part.get("yt_link_with_time"),
                    "source_video": url,
                    "verification_raw": v_info
                }"""

        if old_record in source:
            source = source.replace(old_record, new_record)
            
        cell["source"] = [line + "\n" for line in source.split("\n")]
        # cleanup last newline if split added extra
        if cell["source"][-1] == "\n": cell["source"].pop()
        elif cell["source"][-1].endswith("\n"): cell["source"][-1] = cell["source"][-1][:-1]

with open(notebook_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("Notebook updated for autonomous data enrichment.")
