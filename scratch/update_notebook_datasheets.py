import json
from pathlib import Path

notebook_path = Path("/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/youtube-databaseparts.ipynb")

NEW_SOURCE = """# KOMÓRKA 3
import os
import sys
import json
import time
import subprocess
import re
import csv
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import urllib.request
from typing import List, Optional
from google import genai
from google.genai import types as genai_types
from kaggle_secrets import UserSecretsClient

# --- Zmodyfikowana konfiguracja ścieżek dla Kaggle ---
REPO_NAME = "STRAZ_PRZYSZLOSCI"
BASE_DIR = Path(f"/kaggle/working/{REPO_NAME}/PROJEKTY/13_baza_czesci_recykling/autonomous_test")
RESULTS_FILE = BASE_DIR / "results" / "test_db.jsonl"
INVENTREE_FILE = BASE_DIR / "results" / "inventree_import.jsonl"
ECOEDA_FILE = BASE_DIR / "results" / "ecoEDA_inventory.csv"
HISTORY_FILE = BASE_DIR / "processed_videos.json"
LOG_DIR = BASE_DIR / "logs"

# Upewniamy się, że ścieżki istnieją
RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# === PRIORYTETY ===
PRIORITY_CHANNELS = []

KEYWORDS = [
    "Daniel Rakowiecki naprawa", "serwis elektroniki laptopy", "naprawa telewizora płyta główna",
    "elektrośmieci odzysk części", "naprawa elektroniki AGD moduł", "diagnostyka płyt głównych",
    "wymiana procesora laptop", "naprawa matrycy TV", "serwis RTV elektronika",
    "Krzysztof SQ5RIQ naprawa", "Ivanoe naprawa elektroniki", "naprawa zasilacza TV",
    "elektronika z recyklingu", "naprawa karty graficznej PL", "odzyskiwanie komponentów"
]

class YTPartsExtractor:
    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys
        self.current_key_idx = 0
        self.clients = [genai.Client(api_key=k) for k in api_keys]
        self.MODEL_ANALYSIS = "gemini-3.1-flash-lite-preview" 
        self.MODEL_VERIFICATION = "gemini-3.1-flash-lite-preview" 
        
    def get_client(self):
        client = self.clients[self.current_key_idx]
        self.current_key_idx = (self.current_key_idx + 1) % len(self.clients)
        return client

    def get_video_duration(self, video_path: str) -> float:
        try:
            cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", video_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return float(result.stdout.strip())
        except Exception:
            return 0.0

    def download_pdf(self, part_number: str) -> Optional[str]:
        # Wyszukujemy PDF z datasheet (prosta wyszukiwarka)
        query = f"{part_number} filetype:pdf"
        try:
            url = f"https://html.duckduckgo.com/html/?q={urlencode({'q': query})}"
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8')
                match = re.search(r'href="([^"]+\.pdf)"', html, re.IGNORECASE)
                if match:
                    pdf_url = match.group(1)
                    if pdf_url.startswith('//'): pdf_url = 'https:' + pdf_url
                    
                    pdf_path = f"temp_datasheet_{part_number}.pdf"
                    print(f"📄 Pobieram datasheet dla {part_number}: {pdf_url}")
                    req_pdf = Request(pdf_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urlopen(req_pdf, timeout=15) as pdf_resp:
                        with open(pdf_path, 'wb') as f:
                            f.write(pdf_resp.read())
                    return pdf_path
        except Exception as e:
            print(f"⚠️ Nie udało się pobrać PDF dla {part_number}: {e}")
        return None

    def analyze_datasheet(self, pdf_path: str, part_number: str) -> dict:
        client = self.get_client()
        try:
            pdf_file = client.files.upload(file=pdf_path)
            while pdf_file.state.name == "PROCESSING":
                time.sleep(2)
                pdf_file = client.files.get(name=pdf_file.name)
                
            prompt = (
                f"Wyekstrahuj najważniejsze parametry dla części elektronicznej o numerze '{part_number}' z załączonego PDF. "
                "Zwróć w formacie JSON zgodnym ze specyfikacją InvenTree PartParameters: "
                "{\"parameters\": {\"Voltage\": \"5V\", \"Tolerance\": \"1%\", \"Package\": \"SOT-23\", \"Category\": \"IC\"}}"
            )
            
            contents = [genai_types.Content(role="user", parts=[genai_types.Part.from_uri(file_uri=pdf_file.uri, mime_type=pdf_file.mime_type), genai_types.Part.from_text(text=prompt)])]
            response = client.models.generate_content(model=self.MODEL_VERIFICATION, contents=contents, config=genai_types.GenerateContentConfig(temperature=0.1, response_mime_type="application/json"))
            
            client.files.delete(name=pdf_file.name)
            
            clean_text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(clean_text).get("parameters", {})
        except Exception as e:
            print(f"⚠️ Błąd analizy datasheetu: {e}")
            return {}

    def verify_with_frame(self, high_res_video_path: str, timestamp: int, expected_part_number: str):
        frame_path = f"temp_frame_{timestamp}.jpg"
        print(f"📸 Wycinam klatkę HQ ({timestamp}s)...")
        try:
            subprocess.run(["ffmpeg", "-y", "-ss", str(timestamp), "-i", high_res_video_path, "-vframes", "1", "-q:v", "2", frame_path], capture_output=True)
            if not os.path.exists(frame_path) or os.path.getsize(frame_path) == 0:
                return {"verified": False, "observed_text": "Błąd wycinania klatki"}, "Błąd"

            client = self.get_client()
            with open(frame_path, "rb") as f:
                img_data = f.read()

            prompt = (
                f"Spójrz na tę klatkę w wysokiej rozdzielczości z filmu o naprawie elektroniki. "
                f"1. Dokładnie odczytaj numer seryjny/model układu (np. KBC, chip, kontroler). "
                f"2. Zidentyfikuj typ obudowy (footprint, np. SOT-23, SOIC-8, QFN, BGA). "
                f"3. Podaj krótki opis pinoutu jeśli to możliwe (np. gdzie jest pin 1). "
                f"Model fazy 1 zasugerował: '{expected_part_number}'.\\n"
                f"Odpowiedz TYLKO i WYŁĄCZNIE w formacie JSON:\\n"
                f"{{\\\"verified\\\": true, \\\"observed_text\\\": \\\"NUMER\\\", \\\"footprint\\\": \\\"TYP\\\", \\\"pinout\\\": {{\\\"summary\\\": \\\"OPIS\\\"}}, \\\"datasheet_search_query\\\": \\\"NUMER datasheet pdf\\\", \\\"category\\\": \\\"InvenTree Category\\\"}}"
            )
            
            contents = [genai_types.Content(role="user", parts=[genai_types.Part.from_bytes(data=img_data, mime_type="image/jpeg"), genai_types.Part.from_text(text=prompt)])]
            response = client.models.generate_content(model=self.MODEL_VERIFICATION, contents=contents, config=genai_types.GenerateContentConfig(temperature=0.1, response_mime_type="application/json"))
            os.remove(frame_path)
            
            try:
                clean_text = response.text.replace('```json', '').replace('```', '').strip()
                data = json.loads(clean_text)
                if isinstance(data, list) and len(data) > 0:
                    data = data[0]
                return data, None
            except json.JSONDecodeError:
                return {"verified": False, "observed_text": f"Błąd JSON: {response.text}"}, "Błąd JSON"
        except Exception as e:
            return {"verified": False, "observed_text": f"Błąd API: {str(e)}"}, "Błąd"

    def analyze_video_context(self, video_path: str, youtube_url: str):
        client = self.get_client()
        video_file = client.files.upload(file=video_path)
        print("⏳ Oczekuję na przetworzenie wideo w chmurze Google...")
        while video_file.state.name == "PROCESSING":
            time.sleep(5)
            video_file = client.files.get(name=video_file.name)
        
        is_gemma = "gemma" in self.MODEL_ANALYSIS.lower()
        audio_rules = "Otrzymujesz wideo BEZ DŹWIĘKU." if is_gemma else "Otrzymujesz wideo Z DŹWIĘKIEM. Możesz i powinieneś posiłkować się tym, co mówi serwisant."
        
        system_instruction = f\"\"\"
        Jesteś ekspertem inżynierii odwrotnej. Analizujesz wideo w formacie PROXY (NISKA ROZDZIELCZOŚĆ).
        ZASADY:
        1. {audio_rules}
        2. Twoim zadaniem w tej fazie NIE JEST odczytanie drobnych napisów. 
        3. Szukaj DOKŁADNYCH CZASÓW w których pokazywane są komponenty elektroniczne na zbliżeniu.
        4. Jeśli obraz jest zamazany wpisz obowiązkowo flagę "REQUIRES_HQ_CHECK" jako part_number.
        
        FORMAT WYJŚCIOWY (JSON):
        {{ "device_model": "Model", "detected_parts": [ {{ "part_name": "Nazwa", "part_number": "REQUIRES_HQ_CHECK", "timestamp_seconds": 124, "confidence": 0.9, "context_note": "Opis", "designator": "U1" }} ] }}
        \"\"\"
        
        prompt = f"Przeanalizuj film z YouTube ({youtube_url}). Wyłapuj momenty ekspozycji części elektronicznych."
        contents = [genai_types.Content(role="user", parts=[genai_types.Part.from_uri(file_uri=video_file.uri, mime_type=video_file.mime_type), genai_types.Part.from_text(text=prompt)])]
        
        response = client.models.generate_content(model=self.MODEL_ANALYSIS, contents=contents, config=genai_types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.1, response_mime_type="application/json"))
        
        try:
            client.files.delete(name=video_file.name)
        except:
            pass
        return json.loads(response.text)

    def process_url(self, youtube_url: str):
        base_time = int(time.time())
        video_source = f"temp_source_{base_time}.mp4"
        video_analysis = f"temp_analysis_{base_time}.mp4"
        
        print(f"📥 Pobieram wideo 720p (Single Download Strategy): {youtube_url}...")
        
        subprocess.run([
            "yt-dlp",
            "-f", "bestvideo[height<=720][ext=mp4]/best[height<=720][ext=mp4]", 
            "--merge-output-format", "mp4",
            "-o", video_source, 
            youtube_url
        ], capture_output=True)
        
        if not os.path.exists(video_source):
            print(f"❌ Błąd: yt-dlp nie mógł pobrać filmu.")
            return None

        duration = self.get_video_duration(video_source)
        speed_factor = 1.0
        TARGET_MAX_SECONDS = 800.0 
        
        if duration > TARGET_MAX_SECONDS:
            speed_factor = duration / TARGET_MAX_SECONDS
            print(f"⏱️ Tworzę Time-Lapse {speed_factor:.2f}x do analizy wstępnej...")
            
            subprocess.run([
                "ffmpeg", "-y", "-i", video_source, 
                "-filter:v", f"setpts=PTS/{speed_factor}", 
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28", "-an", video_analysis
            ], capture_output=True)
        else:
            subprocess.run([
                "ffmpeg", "-y", "-i", video_source, "-c", "copy", "-an", video_analysis
            ], capture_output=True)

        try:
            analysis = self.analyze_video_context(video_analysis, youtube_url)
            final_results = []
            if isinstance(analysis, list):
                parts_to_verify = analysis
            elif isinstance(analysis, dict):
                parts_to_verify = analysis.get("detected_parts", [])
            else:
                parts_to_verify = []
            
            for part in parts_to_verify:
                original_ts = int(part.get("timestamp_seconds", 0) * speed_factor)
                part["timestamp_seconds"] = original_ts
                
                ver, err = self.verify_with_frame(video_source, original_ts, part.get("part_number", ""))
                part["verification"] = ver
                
                if isinstance(ver, dict) and ver.get("verified") in [True, False]:
                    obs_text = ver.get("observed_text", "").strip()
                    print(f"   🔍 Potwierdzenie Fazy 2: {obs_text}")
                    if obs_text and obs_text.lower() not in ["", "brak", "nie widzę", "niewyraźne"]:
                        if "błąd" not in obs_text.lower():
                            part["part_number"] = obs_text
                            
                            # PDF Datasheet Fetching & Analysis
                            pdf_path = self.download_pdf(obs_text)
                            if pdf_path:
                                part["datasheet_params"] = self.analyze_datasheet(pdf_path, obs_text)
                                os.remove(pdf_path)
                
                part["yt_link_with_time"] = f"{youtube_url}&t={original_ts}s"
                final_results.append(part)
                
            return {
                "url": youtube_url,
                "device": analysis.get("device_model", "Nieznany Model"),
                "results": final_results
            }
            
        finally:
            for f in [video_source, video_analysis]:
                if os.path.exists(f): os.remove(f)

class YTHunter:
    def __init__(self, yt_api_key: str, gemini_api_keys: list):
        self.yt_api_key = yt_api_key
        self.extractor = YTPartsExtractor(gemini_api_keys)
        self.history = self.load_history()
        
        # Inicjalizacja CSV dla ecoEDA
        if not ECOEDA_FILE.exists():
            with open(ECOEDA_FILE, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Reference", "Value", "Footprint", "Datasheet", "Description"])

    def load_history(self):
        if HISTORY_FILE.exists() and HISTORY_FILE.stat().st_size > 0:
            try:
                with open(HISTORY_FILE, "r") as f:
                    return set(json.load(f))
            except json.JSONDecodeError:
                pass
        return set()

    def save_history(self):
        with open(HISTORY_FILE, "w") as f:
            json.dump(list(self.history), f)

    def get_channel_id(self, channel_identifier: str) -> Optional[str]:
        print(f"📡 Przetwarzam kanał: {channel_identifier}...")
        params = {"part": "snippet", "q": channel_identifier, "type": "channel", "maxResults": 1, "key": self.yt_api_key}
        try:
            with urlopen(Request(f"https://www.googleapis.com/youtube/v3/search?{urlencode(params)}", headers={"Accept": "application/json"}), timeout=30) as resp:
                items = json.loads(resp.read().decode("utf-8")).get("items", [])
                if items: return items[0]["snippet"]["channelId"]
        except: pass
        return None

    def search_videos_by_channel(self, channel_id: str, max_results=5):
        params = {"part": "snippet", "channelId": channel_id, "type": "video", "order": "date", "maxResults": max_results, "key": self.yt_api_key}
        try:
            with urlopen(Request(f"https://www.googleapis.com/youtube/v3/search?{urlencode(params)}", headers={"Accept": "application/json"}), timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8")).get("items", [])
        except: return []

    def search_videos_by_query(self, query: str, max_results=5):
        params = {"part": "snippet", "q": query, "type": "video", "maxResults": max_results, "key": self.yt_api_key, "relevanceLanguage": "pl"}
        try:
            with urlopen(Request(f"https://www.googleapis.com/youtube/v3/search?{urlencode(params)}", headers={"Accept": "application/json"}), timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8")).get("items", [])
        except: return []

    def _process_video_item(self, v_item):
        vid_id = v_item["id"]["videoId"]
        if vid_id in self.history: return
            
        yt_url = f"https://www.youtube.com/watch?v={vid_id}"
        print(f"🎯 Atakuję film: {v_item['snippet']['title']} ({yt_url})")
        
        try:
            result = self.extractor.process_url(yt_url)
            if result and result.get("results"):
                self.save_result(result)
                valid_parts = sum(1 for p in result["results"] if p.get("part_number") != "REQUIRES_HQ_CHECK")
                print(f"✨ Sukces! Zweryfikowano i zapisano {valid_parts} części.")
            
            self.history.add(vid_id)
            self.save_history()
        except Exception as e:
            print(f"⚠️ Błąd podczas przetwarzania {vid_id}: {e}")
        time.sleep(10)

    def hunt(self):
        print("\\n--- ETAP 1: KANAŁY PRIORYTETOWE ---")
        for channel_name in PRIORITY_CHANNELS:
            ch_id = self.get_channel_id(channel_name)
            if ch_id:
                for v in self.search_videos_by_channel(ch_id, max_results=3): self._process_video_item(v)

        print("\\n--- ETAP 2: SŁOWA KLUCZOWE (OGÓLNE YT) ---")
        for kw in KEYWORDS:
            for v in self.search_videos_by_query(kw, max_results=3): self._process_video_item(v)

    def save_result(self, result):
        # Format dla InvenTree
        with open(INVENTREE_FILE, "a", encoding="utf-8") as f_inv:
            for part in result.get("results", []):
                part_number_val = part.get("part_number", "")
                if part_number_val == "REQUIRES_HQ_CHECK": continue
                
                v_info = part.get("verification", {})
                params = part.get("datasheet_params", {})
                
                inventree_record = {
                    "name": part_number_val,
                    "description": part.get("part_name", ""),
                    "category": v_info.get("category", "Uncategorized"),
                    "IPN": part_number_val,
                    "parameters": params,
                    "link": part.get("yt_link_with_time"),
                    "stock_location": result.get("device", "Unknown Device")
                }
                f_inv.write(json.dumps(inventree_record, ensure_ascii=False) + "\\n")
        
        # Format dla ecoEDA CSV
        with open(ECOEDA_FILE, "a", newline="", encoding="utf-8") as f_eco:
            writer = csv.writer(f_eco)
            for part in result.get("results", []):
                part_number_val = part.get("part_number", "")
                if part_number_val == "REQUIRES_HQ_CHECK": continue
                
                v_info = part.get("verification", {})
                writer.writerow([
                    part.get("designator", "U?"),
                    part_number_val,
                    v_info.get("footprint", ""),
                    f"https://www.google.com/search?q={part_number_val}+datasheet",
                    part.get("part_name", "")
                ])

        # Oryginalny format db
        with open(RESULTS_FILE, "a", encoding="utf-8") as f:
            device = result.get("device", "Unknown")
            url = result.get("url", "")
            for part in result.get("results", []):
                part_number_val = part.get("part_number", "")
                if part_number_val == "REQUIRES_HQ_CHECK": continue
                v_info = part.get("verification", {})
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
                    "verification_raw": v_info,
                    "inventree_params": part.get("datasheet_params", {})
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\\n")

# Start
try:
    secrets = UserSecretsClient()
    YT_KEY = secrets.get_secret("YOUTUBE_API_KEY")
    GEMINI_KEYS = [secrets.get_secret("GEMINI_API_KEY")]
    
    hunter = YTHunter(YT_KEY, GEMINI_KEYS)
    print("🚦 Start Autonomicznego Łowcy Części (Wersja Kaggle Cloud + ecoEDA + InvenTree)...")
    hunter.hunt()
except Exception as e:
    print(f"❌ Wystąpił błąd: {e}")
"""

with open(notebook_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb["cells"]:
    if cell["cell_type"] == "code" and "YTPartsExtractor" in "".join(cell["source"]):
        cell["source"] = [line + "\n" for line in NEW_SOURCE.split("\n")]
        # usuń ostatni newline żeby nie było śmieci
        if cell["source"][-1] == "\n":
            cell["source"].pop()
        elif cell["source"][-1].endswith("\n"):
            cell["source"][-1] = cell["source"][-1][:-1]

with open(notebook_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("Notebook updated with PDF extraction and InvenTree/ecoEDA alignment.")
