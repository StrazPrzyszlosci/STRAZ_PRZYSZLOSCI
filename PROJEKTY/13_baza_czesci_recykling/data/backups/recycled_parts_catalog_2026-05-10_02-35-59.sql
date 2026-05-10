PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;
PRAGMA defer_foreign_keys=TRUE;

PRAGMA defer_foreign_keys=TRUE;
CREATE TABLE d1_migrations(
		id         INTEGER PRIMARY KEY AUTOINCREMENT,
		name       TEXT UNIQUE,
		applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);
INSERT INTO "d1_migrations" ("id","name","applied_at") VALUES(1,'0001_init.sql','2026-04-12 19:28:09');
INSERT INTO "d1_migrations" ("id","name","applied_at") VALUES(2,'0002_telegram_throttle.sql','2026-04-12 20:44:27');
INSERT INTO "d1_migrations" ("id","name","applied_at") VALUES(3,'0003_telegram_ai.sql','2026-04-13 15:08:38');
INSERT INTO "d1_migrations" ("id","name","applied_at") VALUES(4,'0004_recycled_parts.sql','2026-04-15 01:53:23');
INSERT INTO "d1_migrations" ("id","name","applied_at") VALUES(5,'0005_recycled_parts_catalog.sql','2026-04-15 01:53:23');
INSERT INTO "d1_migrations" ("id","name","applied_at") VALUES(6,'0006_telegram_sessions.sql','2026-04-15 19:01:33');
INSERT INTO "d1_migrations" ("id","name","applied_at") VALUES(7,'0007_telegram_sessions_add_name.sql','2026-04-20 19:20:04');
INSERT INTO "d1_migrations" ("id","name","applied_at") VALUES(8,'0008_recycled_submissions_add_part_number.sql','2026-04-20 20:10:10');
INSERT INTO "d1_migrations" ("id","name","applied_at") VALUES(9,'0009_fts5_recycled_devices.sql','2026-04-20 20:22:01');
INSERT INTO "d1_migrations" ("id","name","applied_at") VALUES(10,'0010_inventree_alignment.sql','2026-04-20 20:22:03');
INSERT INTO "d1_migrations" ("id","name","applied_at") VALUES(11,'0011_recycled_parts_normalized.sql','2026-04-21 19:10:50');
INSERT INTO "d1_migrations" ("id","name","applied_at") VALUES(12,'0012_organization_agent_entities.sql','2026-04-29 21:13:13');
INSERT INTO "d1_migrations" ("id","name","applied_at") VALUES(13,'0013_datasheets_cache.sql','2026-04-29 21:13:13');
INSERT INTO "d1_migrations" ("id","name","applied_at") VALUES(14,'0014_injection_audit_and_package.sql','2026-04-29 21:13:13');
INSERT INTO "d1_migrations" ("id","name","applied_at") VALUES(15,'0015_olx_parts_market.sql','2026-04-29 21:13:13');
INSERT INTO "d1_migrations" ("id","name","applied_at") VALUES(16,'0016_discord_platform.sql','2026-05-08 10:25:30');

PRAGMA defer_foreign_keys=TRUE;
CREATE TABLE datasheets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  part_number TEXT NOT NULL,
  normalized_part_number TEXT NOT NULL,
  part_name TEXT,
  pdf_url TEXT,
  pdf_source TEXT,          
  pdf_file_id TEXT,         
  pdf_hash TEXT,            
  pdf_page_count INTEGER,
  manufacturer TEXT,
  category TEXT,            
  species TEXT,             
  genus TEXT,               
  mounting TEXT,            
  package TEXT,             
  value TEXT,               
  tolerance TEXT,
  voltage_rating TEXT,
  current_rating TEXT,
  power_rating TEXT,
  temperature_range TEXT,
  pinout_json TEXT,         
  parameters TEXT,             
  description TEXT,
  keywords TEXT,
  kicad_symbol TEXT,
  kicad_footprint TEXT,
  kicad_reference TEXT,
  ipn TEXT,                 
  cross_references TEXT,    
  application_notes TEXT,   
  safety_notes TEXT,        
  ai_model TEXT,            
  ai_confidence REAL,       
  analysis_status TEXT NOT NULL DEFAULT 'pending',  
  analysis_error TEXT,      
  last_analyzed_at TEXT,
  analysis_count INTEGER NOT NULL DEFAULT 0,  
  master_part_id INTEGER,   
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(normalized_part_number, pdf_source)
);

PRAGMA defer_foreign_keys=TRUE;
PRAGMA defer_foreign_keys=TRUE;
PRAGMA defer_foreign_keys=TRUE;
PRAGMA defer_foreign_keys=TRUE;
PRAGMA defer_foreign_keys=TRUE;
PRAGMA defer_foreign_keys=TRUE;
PRAGMA defer_foreign_keys=TRUE;
PRAGMA defer_foreign_keys=TRUE;
PRAGMA defer_foreign_keys=TRUE;
PRAGMA defer_foreign_keys=TRUE;
PRAGMA defer_foreign_keys=TRUE;
PRAGMA defer_foreign_keys=TRUE;
PRAGMA defer_foreign_keys=TRUE;
PRAGMA defer_foreign_keys=TRUE;
PRAGMA defer_foreign_keys=TRUE;
PRAGMA defer_foreign_keys=TRUE;
PRAGMA defer_foreign_keys=TRUE;
PRAGMA defer_foreign_keys=TRUE;
PRAGMA defer_foreign_keys=TRUE;
PRAGMA defer_foreign_keys=TRUE;
PRAGMA defer_foreign_keys=TRUE;
PRAGMA defer_foreign_keys=TRUE;
PRAGMA defer_foreign_keys=TRUE;
CREATE TABLE recycled_device_aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    alias TEXT NOT NULL,
    alias_type TEXT NOT NULL DEFAULT 'device_alias',
    source TEXT,
    created_at TEXT NOT NULL,
    UNIQUE (device_id, alias, alias_type),
    FOREIGN KEY (device_id) REFERENCES recycled_devices(id) ON DELETE CASCADE
);

PRAGMA defer_foreign_keys=TRUE;
CREATE TABLE recycled_device_evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    part_id INTEGER,
    source_type TEXT NOT NULL,
    source_url TEXT,
    excerpt TEXT,
    confidence REAL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (device_id) REFERENCES recycled_devices(id) ON DELETE CASCADE,
    FOREIGN KEY (part_id) REFERENCES recycled_parts(id) ON DELETE SET NULL
);

PRAGMA defer_foreign_keys=TRUE;
CREATE TABLE recycled_device_parts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    master_part_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    designator TEXT NOT NULL DEFAULT '',
    source_url TEXT,
    confidence REAL,
    stock_location TEXT NOT NULL DEFAULT '',
    evidence_url TEXT,
    evidence_timecode REAL,
    created_at TEXT NOT NULL,
    UNIQUE(device_id, master_part_id, designator, stock_location),
    FOREIGN KEY (device_id) REFERENCES recycled_devices(id) ON DELETE CASCADE,
    FOREIGN KEY (master_part_id) REFERENCES recycled_part_master(id) ON DELETE CASCADE
);

PRAGMA defer_foreign_keys=TRUE;
PRAGMA defer_foreign_keys=TRUE;
CREATE TABLE recycled_devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model TEXT UNIQUE NOT NULL,
    brand TEXT,
    description TEXT,
    teardown_url TEXT,
    created_at TEXT NOT NULL
, device_category TEXT, source_url TEXT, donor_rank REAL);

PRAGMA defer_foreign_keys=TRUE;
CREATE TABLE recycled_part_aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_id INTEGER NOT NULL,
    alias TEXT NOT NULL,
    alias_type TEXT NOT NULL DEFAULT 'part_alias',
    source TEXT,
    created_at TEXT NOT NULL,
    UNIQUE (part_id, alias, alias_type),
    FOREIGN KEY (part_id) REFERENCES recycled_parts(id) ON DELETE CASCADE
);

PRAGMA defer_foreign_keys=TRUE;
CREATE TABLE recycled_part_master (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_slug TEXT NOT NULL UNIQUE,
    part_number TEXT NOT NULL,
    normalized_part_number TEXT NOT NULL,
    part_name TEXT NOT NULL,
    species TEXT,
    genus TEXT,
    mounting TEXT,
    value TEXT,
    description TEXT,
    keywords TEXT,
    datasheet_url TEXT,
    datasheet_file_id TEXT,
    ipn TEXT,
    category TEXT,
    parameters TEXT,
    kicad_symbol TEXT,
    kicad_footprint TEXT,
    kicad_reference TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
, package TEXT);
INSERT INTO "recycled_part_master" ("id","part_slug","part_number","normalized_part_number","part_name","species","genus","mounting","value","description","keywords","datasheet_url","datasheet_file_id","ipn","category","parameters","kicad_symbol","kicad_footprint","kicad_reference","created_at","updated_at","package") VALUES(1,'lm3886','LM3886','LM3886','LM3886','Audio Power Amplifier','Linear','Through-hole','68W','High-Performance 68W Audio Power Amplifier with Mute','Audio, Amplifier, Power, Mute, SPiKe, TO-220, lm3886, LM3886, LM3886T/NOPB','','BQACAgQAAxkBAAIGoGn_HJzBPqyedSZ8y0LyH0i5VgABsAACEh4AAl3ZAAFQZsQKwKqMWCs7BA','','Integrated Circuits','{"Voltage":"20V to 94V","Output Power":"68W","THD+N":"0.03%","Signal-to-Noise Ratio":"92dB","Package":"11-Lead TO-220","SNR":"92dB","Supply Voltage":"20V to 84V"}','LM3886','TO-220-11_Vertical','U','2026-04-21T19:29:50.274Z','2026-05-09T11:48:00.700Z',NULL);
INSERT INTO "recycled_part_master" ("id","part_slug","part_number","normalized_part_number","part_name","species","genus","mounting","value","description","keywords","datasheet_url","datasheet_file_id","ipn","category","parameters","kicad_symbol","kicad_footprint","kicad_reference","created_at","updated_at","package") VALUES(2,'tda7294','Tda7294','TDA7294','Tda7294','Audio Amplifier','Class AB Audio Power Amplifier','Through-hole','100W','100 V, 100 W DMOS audio amplifier with mute/st-by','audio, amplifier, DMOS, class AB, mute, standby, multiwatt15, tda7294, TDA7294, multiwatt','','BQACAgQAAxkBAAIEd2nn-yIl3CgXPycJLauQwY51rnZMAAJuHQACgLVBU2eYW2WICbe2OwQ','','Integrated Circuits','{"Supply Voltage":"± 50 V","Output Power":"100 W","Operating Temperature":"0 to 70 °C","Package":"Multiwatt15"}','Amplifier_Audio:TDA7294','Package_TO_SOT_Packages_THT:Multiwatt-15_Vertical','U','2026-04-21T19:33:43.367Z','2026-05-09T10:52:10.883Z',NULL);
INSERT INTO "recycled_part_master" ("id","part_slug","part_number","normalized_part_number","part_name","species","genus","mounting","value","description","keywords","datasheet_url","datasheet_file_id","ipn","category","parameters","kicad_symbol","kicad_footprint","kicad_reference","created_at","updated_at","package") VALUES(3,'93cw44df-4k66','93CW44DF-4K66','93CW44DF-4K66','Mikrokontroler','','','','','8-bitowy mikrokontroler z serii TLCS-870/C firmy Toshiba','Mikrokontroler, 93CW44DF-4K66, Układy scalone','','','','Układy scalone','{"Architecture":"8-bit","Manufacturer":"Toshiba"}','','','','2026-04-21T22:18:05.465Z','2026-04-21T22:18:10.521Z',NULL);
INSERT INTO "recycled_part_master" ("id","part_slug","part_number","normalized_part_number","part_name","species","genus","mounting","value","description","keywords","datasheet_url","datasheet_file_id","ipn","category","parameters","kicad_symbol","kicad_footprint","kicad_reference","created_at","updated_at","package") VALUES(4,'pt4st6ep','Pt4st6ep','PT4ST6EP','Pt4st6ep','','','','','','','','','','','{}','','','','2026-04-23T17:52:45.361Z','2026-04-23T17:52:45.361Z',NULL);
INSERT INTO "recycled_part_master" ("id","part_slug","part_number","normalized_part_number","part_name","species","genus","mounting","value","description","keywords","datasheet_url","datasheet_file_id","ipn","category","parameters","kicad_symbol","kicad_footprint","kicad_reference","created_at","updated_at","package") VALUES(5,'https-datasheet4u-com-pdf-1319877-pt4516','https://datasheet4u.com/pdf/1319877/PT4516','HTTPS//DATASHEET4U.COM/PDF/1319877/PT4516','https://datasheet4u.com/pdf/1319877/PT4516','','','','','','','','','','','{}','','','','2026-04-23T18:11:31.582Z','2026-04-23T18:11:31.582Z',NULL);
INSERT INTO "recycled_part_master" ("id","part_slug","part_number","normalized_part_number","part_name","species","genus","mounting","value","description","keywords","datasheet_url","datasheet_file_id","ipn","category","parameters","kicad_symbol","kicad_footprint","kicad_reference","created_at","updated_at","package") VALUES(6,'sy7658','SY7658','SY7658','SY7658','','','','','High-efficiency step-up DC-DC converter (boost regulator)','SY7658, Integrated Circuit','','','','Integrated Circuit','{"Type":"Boost Regulator","Package":"SOT23-6"}','','','','2026-04-30T20:00:38.905Z','2026-05-09T11:14:40.481Z',NULL);
INSERT INTO "recycled_part_master" ("id","part_slug","part_number","normalized_part_number","part_name","species","genus","mounting","value","description","keywords","datasheet_url","datasheet_file_id","ipn","category","parameters","kicad_symbol","kicad_footprint","kicad_reference","created_at","updated_at","package") VALUES(7,'82uf450v','82uF 450V','82UF450V','kondensator elektrolityczny','','','','','Wysokonapięciowy kondensator elektrolityczny','kondensator elektrolityczny, 82uF 450V, komponenty elektroniczne','','','','komponenty elektroniczne','{"Voltage":"450V","Capacitance":"82uF"}','','','','2026-05-08T20:30:51.043Z','2026-05-08T20:30:58.952Z',NULL);
INSERT INTO "recycled_part_master" ("id","part_slug","part_number","normalized_part_number","part_name","species","genus","mounting","value","description","keywords","datasheet_url","datasheet_file_id","ipn","category","parameters","kicad_symbol","kicad_footprint","kicad_reference","created_at","updated_at","package") VALUES(8,'2026-05-09-sy7658','SY7658','SY7658','SY7658','Battery Charger and Boost Converter','Power Management','SMD','N/A','Single-chip solution for TWS earphone charging cases, integrating charging management, LED power display, and synchronous boost discharge management.','TWS, Charger, Boost, Power Management, ESOP8, Battery, 2026_05_09_SY7658, SY7658, Battery Charger, Boost Converter','','BQACAgQAAxkBAAIGqWn_HWKgRzRNp5XJ46JQ4_ikDW4EAAIUHgACXdkAAVCi08WHTe996DsE','','Power Management IC','{"Input Voltage":"2.9V to 5.5V","Output Voltage":"5.05V","Charging Current":"0.2A/0.5A","Boost Efficiency":"91%","Package":"ESOP8","Operating Temperature":"-20°C to 85°C","Charging Voltage":"4.2V","Boost Output Voltage":"5.05V","Max Boost Output Current":"0.5A","Efficiency":"91%","Switching Frequency":"1MHz"}','SY7658','Package_SO:ESOP-8_3.9x4.9mm_P1.27mm_EP2.29x2.29mm','U','2026-05-09T11:34:39.809Z','2026-05-09T11:41:44.164Z',NULL);
INSERT INTO "recycled_part_master" ("id","part_slug","part_number","normalized_part_number","part_name","species","genus","mounting","value","description","keywords","datasheet_url","datasheet_file_id","ipn","category","parameters","kicad_symbol","kicad_footprint","kicad_reference","created_at","updated_at","package") VALUES(9,'pinoutnagonik','pinout na głośnik','PINOUTNAGONIK','pinout na głośnik','','','','','','','','','','','{}','','','','2026-05-09T11:44:34.795Z','2026-05-09T11:44:34.795Z',NULL);
INSERT INTO "recycled_part_master" ("id","part_slug","part_number","normalized_part_number","part_name","species","genus","mounting","value","description","keywords","datasheet_url","datasheet_file_id","ipn","category","parameters","kicad_symbol","kicad_footprint","kicad_reference","created_at","updated_at","package") VALUES(10,'2026-05-09-sy76582','SY7658','SY7658','SY7658','Battery Charger and Boost Converter','Power Management','SMD','N/A','Single-chip solution for TWS earphone charging cases, integrating charging management, LED display, and synchronous boost discharge management.','TWS, Battery Charger, Boost Converter, Power Management, ESOP8, 2026_05_09_SY7658 (2), SY7658','','BQACAgQAAxkBAAIHBWn_NYIbEkVfgdzqbrspE7PzMRsQAAI_HgACXdkAAVC1v-NeE2-SMzsE','','Power Management IC','{"Input Voltage":"2.9V to 5.5V","Charging Voltage":"4.2V","Boost Output Voltage":"5.05V","Max Output Current":"0.5A","Charging Current":"200mA/500mA","Efficiency":"91%","Package":"ESOP8","Operating Temperature":"-40°C to 125°C","Max Boost Output Current":"0.5A","Switching Frequency":"1MHz"}','SY7658','Package_SO:ESOP-8_3.9x4.9mm_P1.27mm_EP2.29x3.18mm','U','2026-05-09T11:49:37.071Z','2026-05-09T13:24:33.485Z',NULL);

PRAGMA defer_foreign_keys=TRUE;
CREATE TABLE recycled_parts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    part_name TEXT NOT NULL,
    species TEXT, 
    value TEXT, 
    designator TEXT, 
    description TEXT,
    created_at TEXT NOT NULL, genus TEXT, mounting TEXT, keywords TEXT, kicad_symbol TEXT, kicad_footprint TEXT, datasheet_url TEXT, quantity INTEGER, source_url TEXT, confidence REAL, ipn TEXT, category TEXT, parameters TEXT, datasheet_file_id TEXT, kicad_reference TEXT, stock_location TEXT, master_part_id INTEGER, package TEXT,
    FOREIGN KEY (device_id) REFERENCES recycled_devices(id) ON DELETE CASCADE
);

PRAGMA defer_foreign_keys=TRUE;
CREATE TABLE schema_migrations (
      version TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      applied_at TEXT NOT NULL
    );
INSERT INTO "schema_migrations" ("version","name","applied_at") VALUES('20240508180000-init','Create schema_migrations table','2026-05-08T10:25:39.304Z');
INSERT INTO "schema_migrations" ("version","name","applied_at") VALUES('20240508180001-telegram-limits','Ensure telegram_chat_limits table exists (legacy compat)','2026-05-08T10:25:39.304Z');
INSERT INTO "schema_migrations" ("version","name","applied_at") VALUES('20240508180002-telegram-messages','Ensure telegram_chat_messages table exists (legacy compat)','2026-05-08T10:25:39.304Z');
INSERT INTO "schema_migrations" ("version","name","applied_at") VALUES('20240508180003-telegram-issues','Ensure telegram_issues table exists (legacy compat)','2026-05-08T10:25:39.304Z');
INSERT INTO "schema_migrations" ("version","name","applied_at") VALUES('20240508180004-telegram-issue-throttle','Ensure telegram_issue_throttle table exists (legacy compat)','2026-05-08T10:25:39.304Z');
INSERT INTO "schema_migrations" ("version","name","applied_at") VALUES('20240508180005-telegram-chat-sessions','Ensure telegram_user_sessions table exists (legacy compat)','2026-05-08T10:25:39.304Z');

PRAGMA defer_foreign_keys=TRUE;
PRAGMA defer_foreign_keys=TRUE;
PRAGMA defer_foreign_keys=TRUE;
PRAGMA defer_foreign_keys=TRUE;
PRAGMA defer_foreign_keys=TRUE;
PRAGMA defer_foreign_keys=TRUE;
COMMIT;
