-- Migration: 0013_datasheets_cache.sql
-- Description: Create datasheets table for caching downloaded/analyzed PDF datasheets
-- This avoids re-fetching and re-analyzing the same PDF multiple times
-- and provides a structured store for AI-extracted component parameters

CREATE TABLE IF NOT EXISTS datasheets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  part_number TEXT NOT NULL,
  normalized_part_number TEXT NOT NULL,
  part_name TEXT,
  pdf_url TEXT,
  pdf_source TEXT,          -- LCSC, DigiKey, Mouser, SparkFun, UserUpload
  pdf_file_id TEXT,         -- Telegram file_id if user-uploaded
  pdf_hash TEXT,            -- SHA-256 of PDF content for dedup
  pdf_page_count INTEGER,
  manufacturer TEXT,
  category TEXT,            -- InvenTree category (Capacitor, Resistor, IC, etc.)
  species TEXT,             -- e.g. Electrolytic, Ceramic, MOSFET
  genus TEXT,               -- e.g. Capacitor, Transistor, Diode
  mounting TEXT,            -- SMD, THT, BGA, QFN, etc.
  package TEXT,             -- Footprint (SOT-23, SOIC-8, 0805, etc.)
  value TEXT,               -- e.g. 10uF, 4.7kΩ, 3.3V
  tolerance TEXT,
  voltage_rating TEXT,
  current_rating TEXT,
  power_rating TEXT,
  temperature_range TEXT,
  pinout_json TEXT,         -- JSON: {pin_number: pin_function}
<<<<<<< HEAD
 parameters TEXT, -- JSON: all extracted InvenTree-compatible params (consistent with recycled_part_master.parameters)
=======
  parameters TEXT,             -- JSON: all extracted InvenTree-compatible params
>>>>>>> 5c4d401 (feat: security hardening, market scouting automation, and canary phase closeout)
  description TEXT,
  keywords TEXT,
  kicad_symbol TEXT,
  kicad_footprint TEXT,
  kicad_reference TEXT,
  ipn TEXT,                 -- Internal Part Number
  cross_references TEXT,    -- JSON array of equivalent/replacement parts
  application_notes TEXT,   -- Key application info from datasheet
  safety_notes TEXT,        -- Warnings, absolute max ratings summary
  ai_model TEXT,            -- Which AI model analyzed this (e.g. gemini-3.1-flash)
  ai_confidence REAL,       -- 0.0-1.0 confidence of extraction
  analysis_status TEXT NOT NULL DEFAULT 'pending',  -- pending, analyzing, completed, failed
  analysis_error TEXT,      -- Error message if failed
  last_analyzed_at TEXT,
  analysis_count INTEGER NOT NULL DEFAULT 0,  -- How many times re-analyzed
  master_part_id INTEGER,   -- FK to recycled_part_master if matched
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(normalized_part_number, pdf_source)
);

-- Index for fast lookup by part number
CREATE INDEX IF NOT EXISTS idx_datasheets_part_number
  ON datasheets(normalized_part_number);

-- Index for finding pending analyses
CREATE INDEX IF NOT EXISTS idx_datasheets_status
  ON datasheets(analysis_status, updated_at DESC);

-- Index for category browsing
CREATE INDEX IF NOT EXISTS idx_datasheets_category
  ON datasheets(category, species);

-- Index for dedup by PDF hash
CREATE INDEX IF NOT EXISTS idx_datasheets_pdf_hash
  ON datasheets(pdf_hash);

-- Link: when a datasheet is analyzed, update recycled_part_master
-- This is done application-side, not via FK, to keep flexibility
CREATE INDEX IF NOT EXISTS idx_datasheets_master_part
  ON datasheets(master_part_id);
