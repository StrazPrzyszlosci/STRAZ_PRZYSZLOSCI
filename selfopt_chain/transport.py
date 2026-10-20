#!/usr/bin/env python3
"""Klasy łączności LoRa dla selfopt_chain (wzorzec deadmesh, T48).

Adaptacja semantyki mostu Meshtastic<->MeshCore (remix-lora-bridge) oraz
Adaptive Relay do standardu repo. HUB (darmowe modele przez API) nadzoruje
węzły EDGE (małe modele lokalne) przez sieć LoRa. To komórka jest
store-and-forward SPOOL-em: pakiuje advisory w koperty priorytetowe,
chunkuje je do limitu bajtów LoRa i odkłada w katalogu konsumowanym przez
zewnętrzny most (BLE/radio). Komórka sama NIGDY nie nadaje w eter -
transmisja jest po stronie mostu i pozostaje pod bramką operatora.

Bez zewnetrznych zaleznosci; zero sieci, zero radia, w pelni offline.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from pathlib import Path
from typing import Any

P0_CRITICAL = 0
P1_HIGH = 1
P2_TECHNICAL = 2

PRIORITY_LABELS = {P0_CRITICAL: "P0_KRYTYCZNA", P1_HIGH: "P1_WYSOKI", P2_TECHNICAL: "P2_TECHNICZNA"}

STATE_QUEUED = "QUEUED"
STATE_TRANSMITTING = "TRANSMITTING"
STATE_DELIVERED = "DELIVERED"
STATE_EXPIRED = "EXPIRED"
STATE_FAILED = "FAILED"
DELIVERY_STATES = {STATE_QUEUED, STATE_TRANSMITTING, STATE_DELIVERED, STATE_EXPIRED, STATE_FAILED}

DEFAULT_CRITICAL_KEYWORDS = ["!SOS", "!ALERT", "!EMERGENCY", "SOS", "RATUNEK", "POMOC", "ALARM", "WYPADEK"]

ORIGIN_HUB = "SELFOPT_HUB"
DEST_EDGE = "MESHTASTIC"
DEST_MESH_CORE = "MESHCORE"

HUB_TAG = "[HUB→EDGE]"
EDGE_TAG = "[EDGE→HUB]"

DEFAULT_TTL_MINUTES = 30
DEFAULT_MAX_RETRIES_P0 = 5
DEFAULT_MAX_RETRIES_OTHER = 3

LORA_CHUNK_BYTES = 200
AIRTIME_PREAMBLE_S = 0.35
AIRTIME_PER_BYTE_S = 0.014
TX_WINDOW_S = 5.0
GUARD_TIME_S = 0.8
INTER_FRAME_GAP_S = 0.3


def classify_priority(text: str, keywords: list[str] | None = None) -> int:
    """Kwalifikacja krytyczności wg słów kluczowych (jak BridgeEngine)."""
    upper = (text or "").upper()
    for kw in keywords if keywords is not None else DEFAULT_CRITICAL_KEYWORDS:
        if kw.upper() in upper:
            return P1_HIGH
    return P2_TECHNICAL


def deduplication_hash(origin_code: str, sender: str, text: str) -> str:
    """SHA-256(origin|sender|text.trim().lower()) skrócony do 16 hex - jak w BridgeEngine."""
    clean = f"{origin_code}|{sender}|{text.strip().lower()}"
    return hashlib.sha256(clean.encode("utf-8")).hexdigest()[:16]


def detect_loop(text: str, origin_network: str) -> bool:
    """Hop guard: tag kierunkowy sieci źródłowej = wiadomość zatoczyła pętlę."""
    if origin_network == DEST_EDGE and HUB_TAG in text:
        return True
    if origin_network in (DEST_MESH_CORE, ORIGIN_HUB) and EDGE_TAG in text:
        return True
    return False


def estimate_airtime_s(payload: str) -> float:
    """Airtime LoRa EU868 SF9/BW125: ~350 ms preambuły + ~14 ms/bajt (jak RadioScheduler)."""
    return AIRTIME_PREAMBLE_S + len(payload.encode("utf-8")) * AIRTIME_PER_BYTE_S


def chunk_payload(payload: str, chunk_bytes: int = LORA_CHUNK_BYTES) -> list[str]:
    """Podział ładunku na fragmenty <= chunk_bytes bajtów, bezpieczny dla UTF-8."""
    encoded = payload.encode("utf-8")
    if len(encoded) <= chunk_bytes:
        return [payload]
    chunks: list[str] = []
    start = 0
    while start < len(encoded):
        end = min(start + chunk_bytes, len(encoded))
        while end > start:
            try:
                chunks.append(encoded[start:end].decode("utf-8"))
                start = end
                break
            except UnicodeDecodeError:
                end -= 1
        else:
            raise ValueError("chunk_payload: nie udało się wyznaczyć granicy UTF-8")
    return chunks


class LoraEnvelope:
    """Koperta wiadomości semantycznie zgodna z BridgeMessageEntity mostu."""

    def __init__(
        self,
        payload_text: str,
        *,
        origin_network: str = ORIGIN_HUB,
        destination_network: str = DEST_EDGE,
        sender_node: str = "selfopt_chain",
        destination_node: str | None = None,
        source_channel: int = 0,
        destination_channel: int = 0,
        priority: int | None = None,
        ttl_minutes: int = DEFAULT_TTL_MINUTES,
        now_ms: int | None = None,
    ) -> None:
        if detect_loop(payload_text, origin_network):
            raise ValueError("detect_loop: wiadomość z tagiem sieci źródłowej (hop guard) - odrzucono")
        received = now_ms if now_ms is not None else int(time.time() * 1000)
        if priority is None:
            priority = classify_priority(payload_text)
        self.id = uuid.uuid4().hex[:16]
        self.deduplication_hash = deduplication_hash(origin_network, sender_node, payload_text)
        self.origin_network = origin_network
        self.destination_network = destination_network
        self.sender_node = sender_node
        self.destination_node = destination_node
        self.source_channel = source_channel
        self.destination_channel = destination_channel
        self.payload_text = payload_text
        self.priority = priority
        self.delivery_state = STATE_QUEUED
        self.retry_count = 0
        self.max_retries = DEFAULT_MAX_RETRIES_P0 if priority == P0_CRITICAL else DEFAULT_MAX_RETRIES_OTHER
        self.received_at_ms = received
        self.expires_at_ms = received + ttl_minutes * 60 * 1000
        self.error_reason: str | None = None
        self.chunks = len(chunk_payload(payload_text))
        self.estimated_airtime_s = round(estimate_airtime_s(payload_text), 3)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "deduplication_hash": self.deduplication_hash,
            "origin_network": self.origin_network,
            "destination_network": self.destination_network,
            "sender_node": self.sender_node,
            "destination_node": self.destination_node,
            "source_channel": self.source_channel,
            "destination_channel": self.destination_channel,
            "payload_text": self.payload_text,
            "priority": self.priority,
            "priority_label": PRIORITY_LABELS[self.priority],
            "delivery_state": self.delivery_state,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "received_at_ms": self.received_at_ms,
            "expires_at_ms": self.expires_at_ms,
            "error_reason": self.error_reason,
            "chunks": self.chunks,
            "estimated_airtime_s": self.estimated_airtime_s,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LoraEnvelope":
        env = cls(
            data["payload_text"],
            origin_network=data["origin_network"],
            destination_network=data["destination_network"],
            sender_node=data["sender_node"],
            destination_node=data.get("destination_node"),
            source_channel=data.get("source_channel", 0),
            destination_channel=data.get("destination_channel", 0),
            priority=data["priority"],
            ttl_minutes=max(0, (data["expires_at_ms"] - data["received_at_ms"]) // 60000),
            now_ms=data["received_at_ms"],
        )
        env.id = data["id"]
        env.deduplication_hash = data["deduplication_hash"]
        env.delivery_state = data["delivery_state"]
        env.retry_count = data.get("retry_count", 0)
        env.error_reason = data.get("error_reason")
        return env

    def is_expired(self, now_ms: int | None = None) -> bool:
        now = now_ms if now_ms is not None else int(time.time() * 1000)
        return now >= self.expires_at_ms


class LoraSpool:
    """Store-and-forward kolejka spool (katalog) konsumowana przez most LoRa.

    Pliki: spool_dir/queue.jsonl (wszystkie koperty, stany) oraz
    spool_dir/outbox/<id>.json (do nadania). Komórka nie nadaje w eter.
    """

    def __init__(self, spool_dir: Path) -> None:
        self.dir = Path(spool_dir)
        self.queue_path = self.dir / "queue.jsonl"
        self.outbox_dir = self.dir / "outbox"
        self._seen_hashes: set[str] = set()

    def _load(self) -> list[LoraEnvelope]:
        if not self.queue_path.exists():
            return []
        envelopes: list[LoraEnvelope] = []
        for line in self.queue_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                envelopes.append(LoraEnvelope.from_dict(json.loads(line)))
        return envelopes

    def _save(self, envelopes: list[LoraEnvelope]) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        self.queue_path.write_text(
            "".join(json.dumps(e.to_dict(), ensure_ascii=False) + "\n" for e in envelopes),
            encoding="utf-8",
        )

    def enqueue(self, envelope: LoraEnvelope, *, now_ms: int | None = None) -> dict[str, Any]:
        """Dedup + zapis do kolejki + wystawienie pliku outbox do nadania.

        Expiry liczone wzgledem czasu referencyjnego: jawnie przekazanego
        now_ms albo received_at_ms koperty (zegar wstrzykniety przy tworzeniu).
        Stare koperty sprzata expire_old_messages() po stronie konsumenta.
        """
        now = now_ms if now_ms is not None else envelope.received_at_ms
        if envelope.deduplication_hash in self._seen_hashes:
            return {"enqueued": False, "reason": "duplicate_dedup_hash", "id": envelope.id}
        existing = self._load()
        if any(e.deduplication_hash == envelope.deduplication_hash for e in existing):
            return {"enqueued": False, "reason": "duplicate_dedup_hash", "id": envelope.id}
        if envelope.is_expired(now):
            envelope.delivery_state = STATE_EXPIRED
            existing.append(envelope)
            self._save(existing)
            return {"enqueued": False, "reason": "expired", "id": envelope.id}
        existing.append(envelope)
        self._save(existing)
        self.outbox_dir.mkdir(parents=True, exist_ok=True)
        (self.outbox_dir / f"{envelope.id}.json").write_text(
            json.dumps(envelope.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        self._seen_hashes.add(envelope.deduplication_hash)
        return {"enqueued": True, "reason": "queued_for_bridge", "id": envelope.id}

    def mark_state(self, envelope_id: str, state: str, error_reason: str | None = None) -> bool:
        if state not in DELIVERY_STATES:
            raise ValueError(f"mark_state: nieznany stan {state}")
        envelopes = self._load()
        for e in envelopes:
            if e.id == envelope_id:
                e.delivery_state = state
                if error_reason:
                    e.error_reason = error_reason
                self._save(envelopes)
                return True
        return False

    def expire_old_messages(self, now_ms: int | None = None) -> int:
        now = now_ms if now_ms is not None else int(time.time() * 1000)
        envelopes = self._load()
        expired = 0
        for e in envelopes:
            if e.delivery_state in (STATE_QUEUED, STATE_TRANSMITTING) and e.is_expired(now):
                e.delivery_state = STATE_EXPIRED
                expired += 1
        if expired:
            self._save(envelopes)
        return expired

    def pending(self) -> list[LoraEnvelope]:
        return [e for e in self._load() if e.delivery_state == STATE_QUEUED]

    def all_messages(self) -> list[LoraEnvelope]:
        return self._load()

    def tx_plan(self, tx_window_s: float = TX_WINDOW_S, guard_time_s: float = GUARD_TIME_S) -> dict[str, Any]:
        """Plan okna TX wg priorytetów (P0 przed P1 przed P2) + budżet airtime.

        Zwraca hint dla mostu: ile wiadomości zmieści się w oknie TX po
        odjęciu guard time, z odstępem INTER_FRAME_GAP_S między ramkami.
        """
        queue = sorted(self.pending(), key=lambda e: (e.priority, e.received_at_ms))
        usable = max(0.0, tx_window_s - 2 * guard_time_s)
        plan: list[dict[str, Any]] = []
        spent = 0.0
        for e in queue:
            cost = e.estimated_airtime_s + INTER_FRAME_GAP_S
            if spent + cost > usable:
                break
            spent += cost
            plan.append({"id": e.id, "priority": e.priority, "priority_label": PRIORITY_LABELS[e.priority], "airtime_s": e.estimated_airtime_s})
        return {
            "phase": "TX_WINDOW_HINT",
            "tx_window_s": tx_window_s,
            "guard_time_s": guard_time_s,
            "usable_airtime_s": round(usable, 3),
            "planned_airtime_s": round(spent, 3),
            "messages_in_window": len(plan),
            "plan": plan,
        }


def format_advisory_for_edge(node_output: str, *, origin_network: str = ORIGIN_HUB) -> str:
    """Formatowanie ładunku jak w BridgeEngine: tag kierunku + prefix nadawcy."""
    return f"{HUB_TAG} selfopt_chain: {node_output}".strip() if origin_network == ORIGIN_HUB else f"{EDGE_TAG} selfopt_chain: {node_output}".strip()


def sanitize_for_radio(text: str, max_len: int = 1200) -> str:
    """Usuwa znaki kontrolane i przycina ładunek do rozsądnego limitu tekstowego."""
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text or "")
    return cleaned[:max_len]
