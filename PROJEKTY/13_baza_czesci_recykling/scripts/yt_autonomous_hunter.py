#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import subprocess
import argparse
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from typing import List, Dict, Any, Optional

# Importowanie bibliotek Google GenAI
try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    print("BŁĄD: Brak biblioteki google-genai. Zainstaluj: pip install google-genai")
    sys.exit(1)

# --- Konfiguracja ścieżek ---
BASE_DIR = Path("/home/krzysiek/Dokumenty/INFO_GROUP/STRAZ_POLSKIEGO_Ai/PROJEKTY/13_baza_czesci_recykling/autonomous_test")
RESULTS_FILE = BASE_DIR / "results" / "test_db.jsonl"
HISTORY_FILE = BASE_DIR / "processed_videos.json"
LOG_DIR = BASE_DIR / "logs"

# === PRIORYTETY ===
# 1. Konkretne Kanały o największym potencjale (Handles i Usernames z Twojej listy)
PRIORITY_CHANNELS =[
    #"@Kris0725PL",
    "@Mymatevince",
    "@TechCornerTV",
    "@pl.elektronik",
    "@northwestrepair",
    "@TotenSerwisPolska",
    "AdamantComputers",
    "redliquid1",
    "VirtualFutureTV"
]

# 2. Słowa kluczowe (wyszukiwanie ogólne)
KEYWORDS =[
    "Daniel Rakowiecki naprawa", "serwis elektroniki laptopy", "naprawa telewizora płyta główna",
    "elektrośmieci odzysk części", "naprawa elektroniki AGD moduł", "diagnostyka płyt głównych",
    "wymiana procesora laptop", "naprawa matrycy TV", "serwis RTV elektronika",
    "Krzysztof SQ5RIQ naprawa", "Ivanoe naprawa elektroniki", "naprawa zasilacza TV",
    "elektronika z recyklingu", "naprawa karty graficznej PL", "odzyskiwanie komponentów"
]

# ==========================================
# KLASA: YTPartsExtractor (Logika pobierania i AI)
# ==========================================
class YTPartsExtractor:
    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys
        self.current_key_idx = 0
        self.clients =[genai.Client(api_key=k) for k in api_keys]
        
        # WPISZ TUTAJ MODEL:
        # Stabilne Gemini wspierające audio: "gemini-2.5-flash", "gemini-1.5-flash"
        # Modele Gemma (bez audio): "gemma-4-31b-it", "gemma-3-27b-it"
        self.MODEL_ANALYSIS = "gemini-3.1-flash-lite-preview" 
        self.MODEL_VERIFICATION = "gemini-3.1-flash-lite-preview" 
        
    def get_client(self):
        client = self.clients[self.current_key_idx]
        self.current_key_idx = (self.current_key_idx + 1) % len(self.clients)
        return client

    def get_video_duration(self, video_path: str) -> float:
        try:
            cmd =[
                "ffprobe", "-v", "error", "-show_entries",
                "format=duration", "-of",
                "default=noprint_wrappers=1:nokey=1", video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return float(result.stdout.strip())
        except Exception as e:
            print(f"⚠ Nie udało się pobrać długości wideo: {e}")
            return 0.0

    def verify_with_frame(self, high_res_video_path: str, timestamp: int, expected_part_number: str):
        """Faza 2: Skupia się na DOKŁADNYM odczytaniu napisu ze zdjęcia HQ."""
        frame_path = f"temp_frame_{timestamp}.jpg"
        print(f"📸 Wycinam klatkę HQ ({timestamp}s)...")
        
        try:
            subprocess.run([
                "ffmpeg", "-y", "-ss", str(timestamp), "-i", high_res_video_path,
                "-vframes", "1", "-q:v", "2", frame_path
            ], capture_output=True)
            
            if not os.path.exists(frame_path) or os.path.getsize(frame_path) == 0:
                return {"verified": False, "observed_text": "Błąd wycinania klatki"}, "Błąd"

            client = self.get_client()
            with open(frame_path, "rb") as f:
                img_data = f.read()

            # Nowy prompt skupiony na odczycie OCR (nawet jeśli model fazy 1 nic nie odczytał)
            prompt = (
                f"Spójrz na tę klatkę w wysokiej rozdzielczości wyciągniętą z filmu o naprawie elektroniki. "
                f"Twoim jedynym zadaniem jest dokładne odczytanie numerów seryjnych, oznaczeń modeli (np. układów KBC, chipów, modułów) "
                f"lub kodów kreskowych z elementu ukazanego w kadrze.\n"
                f"Model fazy 1 zasugerował: '{expected_part_number}'. Jeśli to 'REQUIRES_HQ_CHECK', zignoruj tę podpowiedź i po prostu odczytaj to co widzisz.\n"
                f"Odpowiedz TYLKO i WYŁĄCZNIE w formacie JSON:\n"
                f"{{\"verified\": true/false, \"observed_text\": \"DOKŁADNY_ODCZYTANY_NUMER_LUB_BRAK\"}}"
            )
            
            contents = [
                genai_types.Content(
                    role="user",
                    parts=[
                        genai_types.Part.from_bytes(data=img_data, mime_type="image/jpeg"),
                        genai_types.Part.from_text(text=prompt)
                    ]
                )
            ]
            
            response = client.models.generate_content(
                model=self.MODEL_VERIFICATION,
                contents=contents,
                config=genai_types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json"
                )
            )
            
            os.remove(frame_path)
            
            try:
                clean_text = response.text.replace('```json', '').replace('```', '').strip()
                return json.loads(clean_text), None
            except json.JSONDecodeError:
                return {"verified": False, "observed_text": f"Błąd JSON: {response.text}"}, "Błąd JSON"
                
        except Exception as e:
            return {"verified": False, "observed_text": f"Błąd API: {str(e)}"}, "Błąd"

    def analyze_video_context(self, video_path: str, youtube_url: str):
        if not os.path.exists(video_path) or os.path.getsize(video_path) < 1000:
            raise Exception(f"BŁĄD: Plik wideo {video_path} nie istnieje.")
            
        client = self.get_client()
        print(f"🚀 Przesyłam wideo do File API: {video_path}")
        video_file = client.files.upload(file=video_path)
        
        print("⏳ Oczekuję na przetworzenie wideo w chmurze Google...")
        while video_file.state.name == "PROCESSING":
            time.sleep(5)
            video_file = client.files.get(name=video_file.name)
        
        if video_file.state.name == "FAILED":
            raise Exception("Błąd przetwarzania wideo przez Google File API.")

        is_gemma = "gemma" in self.MODEL_ANALYSIS.lower()
        audio_rules = "Otrzymujesz wideo BEZ DŹWIĘKU." if is_gemma else "Otrzymujesz wideo Z DŹWIĘKIEM. Możesz i powinieneś posiłkować się tym, co mówi serwisant (np. 'Wymieniamy układ KBC IT8586E')."

        # KOMPLETNIE PRZEBUDOWANY PROMPT (Faza 1 jako Scout / Odkrywca kadrów)
        system_instruction = f"""
        Jesteś ekspertem inżynierii odwrotnej. Analizujesz wideo w formacie PROXY (NISKA ROZDZIELCZOŚĆ).
        
        ZASADY:
        1. {audio_rules}
        2. Twoim zadaniem w tej fazie NIE JEST odczytanie drobnych napisów. Wiesz, że wideo ma niską jakość.
        3. Twoim GŁÓWNYM CELM jest znalezienie DOKŁADNYCH CZASÓW (timestamp w sekundach), w których serwisant pokazuje w kadrze, na zbliżeniu lub na mikroskopie konkretne komponenty (chipy, płyty główne, zasilacze, naklejki znamionowe).
        4. Jeśli zidentyfikujesz taki moment, zapisz go! Podaj nazwę elementu (np. z audio lub wyglądu). 
        5. W polu "part_number", jeśli obraz jest zamazany, ZAMIAST odrzucać element, wpisz obowiązkowo flagę "REQUIRES_HQ_CHECK". My później pobierzemy klatkę w wysokiej rozdzielczości z tego ułamka sekundy i odczytamy ją za Ciebie. Jeśli jednak nazwa padła wyraźnie w audio, wpisz ją.
        
        FORMAT WYJŚCIOWY (JSON):
        {{
          "device_model": "Dokładny model urządzenia (jeśli padł w filmie, inaczej Nieznany)",
          "detected_parts":[
            {{
              "part_name": "Nazwa części (np. układ przetwornicy, matryca, naklejka płyty głównej)",
              "part_number": "Odgadnięty numer LUB 'REQUIRES_HQ_CHECK'",
              "timestamp_seconds": 124,
              "confidence": 0.0-1.0,
              "context_note": "Dlaczego wybrałeś ten moment? Co to za element?"
            }}
          ]
        }}
        """
        
        prompt = f"Przeanalizuj film z YouTube ({youtube_url}). Skup się na wyłapywaniu momentów ekspozycji części elektronicznych. Nie odrzucaj części z powodu niskiej rozdzielczości – użyj flagi REQUIRES_HQ_CHECK."
        print(f"🧠 Analiza multimodalna (Scout) przez {self.MODEL_ANALYSIS} w toku...")
        
        contents =[
            genai_types.Content(
                role="user",
                parts=[
                    genai_types.Part.from_uri(file_uri=video_file.uri, mime_type=video_file.mime_type),
                    genai_types.Part.from_text(text=prompt)
                ]
            )
        ]

        response = client.models.generate_content(
            model=self.MODEL_ANALYSIS,
            contents=contents,
            config=genai_types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.1,
                response_mime_type="application/json"
            )
        )
        
        try:
            client.files.delete(name=video_file.name)
        except Exception:
            pass
            
        return json.loads(response.text)

    def process_url(self, youtube_url: str):
        base_time = int(time.time())
        video_low = f"temp_low_{base_time}.mp4"
        video_high = f"temp_high_{base_time}.mp4"
        high_res_downloaded = False
        is_gemma = "gemma" in self.MODEL_ANALYSIS.lower()
        
        print(f"📥 Pobieram wideo (low-res) do analizy wstępnej: {youtube_url}...")
        subprocess.run([
            "yt-dlp",
            "--cookies-from-browser", "firefox",
            "--remote-components", "ejs:github",
            "--js-runtimes", "node:/home/krzysiek/.nvm/versions/node/v24.13.1/bin/node",
            "-f", "best[height<=360]", 
            "-o", video_low, 
            youtube_url
        ], capture_output=True)
        
        if not os.path.exists(video_low):
            print(f"❌ Błąd: yt-dlp nie mógł pobrać filmu (odrzucony / zablokowany).")
            return None

        duration = self.get_video_duration(video_low)
        speed_factor = 1.0
        TARGET_MAX_SECONDS = 800.0 
        
        if duration > TARGET_MAX_SECONDS:
            speed_factor = duration / TARGET_MAX_SECONDS
            print(f"⏱️ Wideo przekracza limit ({duration:.0f}s). Przyspieszam Time-Lapse {speed_factor:.2f}x...")
            processed_low = f"processed_{video_low}"
            
            if is_gemma:
                print("🔇 Model Gemma -> Usuwam audio podczas kompresji.")
                subprocess.run([
                    "ffmpeg", "-y", "-i", video_low, 
                    "-filter:v", f"setpts=PTS/{speed_factor}", 
                    "-c:v", "libx264", "-preset", "ultrafast", "-an", processed_low
                ], capture_output=True)
            else:
                print("🔊 Model Gemini -> Kompresuję Wideo + Audio (zachowanie synchronizacji)...")
                atempos =[]
                rem_speed = speed_factor
                while rem_speed > 2.0:
                    atempos.append("atempo=2.0")
                    rem_speed /= 2.0
                if rem_speed > 1.0:
                    atempos.append(f"atempo={rem_speed:.4f}")
                atempo_str = ",".join(atempos) if atempos else "atempo=1.0"
                
                try:
                    subprocess.run([
                        "ffmpeg", "-y", "-i", video_low, 
                        "-filter_complex", f"[0:v]setpts=PTS/{speed_factor}[v];[0:a]{atempo_str}[a]", 
                        "-map", "[v]", "-map", "[a]",
                        "-c:v", "libx264", "-preset", "ultrafast", processed_low
                    ], check=True, capture_output=True)
                except subprocess.CalledProcessError:
                    print("⚠️ Błąd filtru audio. Zrzucam audio (Tryb Fallback).")
                    subprocess.run([
                        "ffmpeg", "-y", "-i", video_low, 
                        "-filter:v", f"setpts=PTS/{speed_factor}", 
                        "-c:v", "libx264", "-preset", "ultrafast", "-an", processed_low
                    ], capture_output=True)
                    
            if os.path.exists(processed_low):
                os.replace(processed_low, video_low)
        else:
            if is_gemma:
                print("🔇 Model Gemma -> Usuwam ścieżkę dźwiękową (natywnie).")
                silent_low = f"silent_{video_low}"
                subprocess.run([
                    "ffmpeg", "-y", "-i", video_low, 
                    "-c:v", "copy", "-an", silent_low
                ], capture_output=True)
                if os.path.exists(silent_low):
                    os.replace(silent_low, video_low)

        try:
            analysis = self.analyze_video_context(video_low, youtube_url)
            final_results =[]
            
            # Pobieramy do weryfikacji wszystkie części wykryte przez model w Fazie 1.
            # Skoro kazaliśmy mu wstawiać REQUIRES_HQ_CHECK, to bierzemy je wszystkie pod uwagę.
            parts_to_verify = analysis.get("detected_parts",[])
            
            if parts_to_verify:
                print(f"🌟 Znaleziono {len(parts_to_verify)} potencjalnych kadrów! Pobieram wideo High-Res...")
                subprocess.run([
                    "yt-dlp",
                    "--cookies-from-browser", "firefox",
                    "--remote-components", "ejs:github",
                    "--js-runtimes", "node:/home/krzysiek/.nvm/versions/node/v24.13.1/bin/node",
                    "-f", "bestvideo[height<=720][ext=mp4]/best[height<=720][ext=mp4]", 
                    "--merge-output-format", "mp4", 
                    "-o", video_high, 
                    youtube_url
                ], capture_output=True)
                high_res_downloaded = os.path.exists(video_high)
            else:
                print(f"⏭ {self.MODEL_ANALYSIS} nie znalazł w Fazie 1 żadnych ciekawych kadrów z elektroniką.")

            for part in parts_to_verify:
                original_ts = int(part.get("timestamp_seconds", 0) * speed_factor)
                part["timestamp_seconds"] = original_ts
                
                if high_res_downloaded:
                    ver, err = self.verify_with_frame(video_high, original_ts, part.get("part_number", ""))
                    part["verification"] = ver
                    
                    if ver and ver.get("verified") in [True, False]:
                        obs_text = ver.get("observed_text", "").strip()
                        
                        # DODANA LINIJKA - INFORMACJA Z FAZY 2:
                        print(f"   🔍 Faza 2 (HQ) odczytała: {obs_text}")
                        
                        if obs_text and obs_text.lower() not in ["", "brak", "nie widzę", "niewyraźne"]:
                            # Nie nadpisuj, jeśli API rzuciło błędem
                            if "błąd" not in obs_text.lower():
                                part["part_number"] = obs_text
                else:
                    part["verification"] = {"verified": False, "observed_text": "Brak pliku High-Res do weryfikacji"}
                    print("   ❌ Pominięto weryfikację Fazy 2 (Brak wideo HQ)")
                
                part["yt_link_with_time"] = f"{youtube_url}&t={original_ts}s"
                final_results.append(part)
                
            return {
                "url": youtube_url,
                "device": analysis.get("device_model", "Nieznany Model"),
                "results": final_results
            }
            
        finally:
            if os.path.exists(video_low):
                os.remove(video_low)
            if high_res_downloaded and os.path.exists(video_high):
                os.remove(video_high)


# ==========================================
# KLASA: YTHunter (Orkiestrator API i Przeszukiwania)
# ==========================================
class YTHunter:
    def __init__(self, yt_api_key: str, gemini_api_keys: list):
        self.yt_api_key = yt_api_key
        self.extractor = YTPartsExtractor(gemini_api_keys)
        self.history = self.load_history()

    def load_history(self):
        RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        if HISTORY_FILE.exists() and HISTORY_FILE.stat().st_size > 0:
            try:
                with open(HISTORY_FILE, "r") as f:
                    return set(json.load(f))
            except json.JSONDecodeError:
                return set()
        return set()

    def save_history(self):
        with open(HISTORY_FILE, "w") as f:
            json.dump(list(self.history), f)

    def get_channel_id(self, channel_identifier: str) -> Optional[str]:
        """Tłumaczy nazwę użytkownika lub @handle na oficjalny ID kanału (UC...)"""
        print(f"📡 Przetwarzam kanał: {channel_identifier}...")
        params = {
            "part": "snippet",
            "q": channel_identifier,
            "type": "channel",
            "maxResults": 1,
            "key": self.yt_api_key
        }
        url = f"https://www.googleapis.com/youtube/v3/search?{urlencode(params)}"
        req = Request(url, headers={"Accept": "application/json"})
        try:
            with urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                items = data.get("items",[])
                if items:
                    return items[0]["snippet"]["channelId"]
        except Exception as e:
            print(f"❌ Błąd weryfikacji ID kanału {channel_identifier}: {e}")
        return None

    def search_videos_by_channel(self, channel_id: str, max_results=5):
        """Pobiera najnowsze filmy bezpośrednio ze wskazanego kanału"""
        params = {
            "part": "snippet",
            "channelId": channel_id,
            "type": "video",
            "order": "date", # Sortuj od najnowszych
            "maxResults": max_results,
            "key": self.yt_api_key
        }
        url = f"https://www.googleapis.com/youtube/v3/search?{urlencode(params)}"
        req = Request(url, headers={"Accept": "application/json"})
        try:
            with urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("items",[])
        except Exception as e:
            print(f"❌ Błąd pobierania filmów z kanału {channel_id}: {e}")
            return[]

    def search_videos_by_query(self, query: str, max_results=5):
        """Standardowe wyszukiwanie wideo po frazie kluczowej na całym YT"""
        print(f"🔍 Szukam na YT frazy: {query}")
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": max_results,
            "key": self.yt_api_key,
            "relevanceLanguage": "pl" if any(c in query.lower() for c in "ąćęłńóśźż") else "en"
        }
        url = f"https://www.googleapis.com/youtube/v3/search?{urlencode(params)}"
        req = Request(url, headers={"Accept": "application/json"})
        try:
            with urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("items",[])
        except Exception as e:
            print(f"❌ Błąd wyszukiwania: {e}")
            return[]

    def _process_video_item(self, v_item):
        """Główny blok do ekstrakcji i zapisu pojedynczego wideo"""
        vid_id = v_item["id"]["videoId"]
        if vid_id in self.history:
            print(f"⏭️ Pomijam (już w bazie): {vid_id}")
            return
            
        # Nareszcie i definitywnie zaimplementowany pełny link!
        yt_url = f"https://www.youtube.com/watch?v={vid_id}"
        print(f"🎯 Atakuję film: {v_item['snippet']['title']} ({yt_url})")
        
        try:
            result = self.extractor.process_url(yt_url)
            
            if result and result.get("results"):
                self.save_result(result)
                
                # Podliczamy te części, które nie są zignorowane ("REQUIRES_HQ_CHECK" bez poprawki z Fazy 2)
                valid_parts = sum(1 for p in result["results"] if p.get("part_number") != "REQUIRES_HQ_CHECK")
                
                print(f"✨ Sukces! Zweryfikowano i zapisano do bazy {valid_parts} części (z {len(result['results'])} pobranych kadrów).")
            else:
                print(f"ℹ️ Brak użytecznych numerów części na wideo {vid_id}.")
            
            self.history.add(vid_id)
            self.save_history()
            
        except Exception as e:
            print(f"⚠️ Błąd podczas przetwarzania {vid_id}: {e}")
        
        # Pauza bezpieczeństwa dla limitów API
        time.sleep(10)

    def hunt(self):
        print("\n--- ETAP 1: KANAŁY PRIORYTETOWE ---")
        for channel_name in PRIORITY_CHANNELS:
            ch_id = self.get_channel_id(channel_name)
            if not ch_id:
                continue
                
            print(f"✅ Znaleziono ID dla {channel_name}: {ch_id}. Pobieram bazę najnowszych filmów...")
            videos = self.search_videos_by_channel(ch_id, max_results=5) 
            for v in videos:
                self._process_video_item(v)

        print("\n--- ETAP 2: SŁOWA KLUCZOWE (OGÓLNE YT) ---")
        for kw in KEYWORDS:
            videos = self.search_videos_by_query(kw)
            for v in videos:
                self._process_video_item(v)

    def save_result(self, result):
        with open(RESULTS_FILE, "a", encoding="utf-8") as f:
            device = result.get("device", "Unknown")
            url = result.get("url", "")
            
            for part in result.get("results",[]):
                # Filtrujemy do bazy wyniki, które mają jaki-taki odczyt (nie są czystymi placeholderami)
                part_number_val = part.get("part_number", "")
                if part_number_val == "REQUIRES_HQ_CHECK":
                    continue # Faza 2 nic nie poprawiła, pomijamy śmieć w pliku finalnym
                    
                record = {
                    "timestamp_db": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "device": device,
                    "part_name": part.get("part_name"),
                    "part_number": part_number_val,
                    "confidence": part.get("confidence", 0.0),
                    "yt_link": part.get("yt_link_with_time"),
                    "verification": part.get("verification", {}),
                    "source_video": url
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ==========================================
# MAIN ROUTINE
# ==========================================
if __name__ == "__main__":
    YT_KEY = os.environ.get("YOUTUBE_API_KEY")
    GEMINI_KEYS =[os.environ.get("GEMINI_API_KEY")]

    if not YT_KEY or not GEMINI_KEYS[0]:
        print("❌ Brak kluczy API (YOUTUBE_API_KEY / GEMINI_API_KEY)!")
        sys.exit(1)

    hunter = YTHunter(YT_KEY, GEMINI_KEYS)
    print("🚦 Start Autonomicznego Łowcy Części (2-Fazowy Agent HQ)...")
    hunter.hunt()