import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from selfopt_chain import transport
from selfopt_chain.transport import (
    LoraEnvelope,
    LoraSpool,
    P0_CRITICAL,
    P1_HIGH,
    P2_TECHNICAL,
    chunk_payload,
    classify_priority,
    deduplication_hash,
    detect_loop,
    estimate_airtime_s,
    format_advisory_for_edge,
    sanitize_for_radio,
)


class ClassifyPriorityTest(unittest.TestCase):
    def test_alarm_keywords_promote_to_p1(self):
        for text in ("ALARM: pompa B padla", "wezwanie SOS z pola", "!ALERT temp"):
            self.assertEqual(classify_priority(text), P1_HIGH)

    def test_technical_text_stays_p2(self):
        self.assertEqual(classify_priority("rutynowe podsumowanie telemetrii"), P2_TECHNICAL)


class DedupAndLoopTest(unittest.TestCase):
    def test_dedup_hash_stable_and_16_hex(self):
        h1 = deduplication_hash("SELFOPT_HUB", "node-a", "Alarm Temp 27C")
        h2 = deduplication_hash("SELFOPT_HUB", "node-a", "  alarm temp 27c ")
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 16)
        self.assertFalse(deduplication_hash("SELFOPT_HUB", "node-a", "x") == deduplication_hash("SELFOPT_HUB", "node-b", "x"))

    def test_detect_loop_hub_tag_in_edge_origin(self):
        self.assertTrue(detect_loop("[HUB→EDGE] selfopt_chain: x", transport.DEST_EDGE))
        self.assertTrue(detect_loop("[EDGE→HUB] node: x", transport.ORIGIN_HUB))
        self.assertFalse(detect_loop("[HUB→EDGE] x", transport.ORIGIN_HUB))
        self.assertFalse(detect_loop("[EDGE→HUB] x", transport.DEST_EDGE))


class AirtimeAndChunkingTest(unittest.TestCase):
    def test_airtime_formula_matches_bridge(self):
        payload = "A" * 100
        self.assertAlmostEqual(estimate_airtime_s(payload), 0.35 + 100 * 0.014)

    def test_short_payload_single_chunk(self):
        self.assertEqual(chunk_payload("krotka wiadomosc"), ["krotka wiadomosc"])

    def test_utf8_safe_chunking_and_reassembly(self):
        payload = "ąćęłńóśźż" * 50
        chunks = chunk_payload(payload, 200)
        for chunk in chunks:
            self.assertLessEqual(len(chunk.encode("utf-8")), 200)
        self.assertEqual("".join(chunks), payload)

    def test_multibyte_boundary_is_not_broken(self):
        payload = "ż" * 201
        chunks = chunk_payload(payload, 200)
        for chunk in chunks:
            chunk.encode("utf-8")


class EnvelopeTest(unittest.TestCase):
    def test_priority_inference_and_retries(self):
        alarm = LoraEnvelope("ALARM: czujnik B zgasl", now_ms=1_000_000)
        self.assertEqual(alarm.priority, P1_HIGH)
        self.assertEqual(alarm.max_retries, 3)
        p0 = LoraEnvelope("SOS z pola", priority=P0_CRITICAL, now_ms=1_000_000)
        self.assertEqual(p0.max_retries, 5)
        tech = LoraEnvelope("podsumowanie doby", now_ms=1_000_000)
        self.assertEqual(tech.priority, P2_TECHNICAL)

    def test_ttl_expiry(self):
        env = LoraEnvelope("x", ttl_minutes=30, now_ms=1_000_000)
        self.assertFalse(env.is_expired(now_ms=1_000_000 + 29 * 60 * 1000))
        self.assertTrue(env.is_expired(now_ms=1_000_000 + 31 * 60 * 1000))

    def test_hop_guard_rejects_looped_payload(self):
        with self.assertRaises(ValueError):
            LoraEnvelope("[EDGE→HUB] wracam do huba", origin_network=transport.ORIGIN_HUB)

    def test_to_dict_from_dict_roundtrip(self):
        env = LoraEnvelope("ALARM test", destination_network="MESHCORE", now_ms=1_000_000)
        restored = LoraEnvelope.from_dict(json.loads(json.dumps(env.to_dict())))
        self.assertEqual(restored.deduplication_hash, env.deduplication_hash)
        self.assertEqual(restored.priority, env.priority)
        self.assertEqual(restored.expires_at_ms, env.expires_at_ms)


class SpoolTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.spool = LoraSpool(Path(self.tmp.name) / "spool")

    def test_enqueue_creates_outbox_and_queue(self):
        env = LoraEnvelope("ALARM: poziom wody", now_ms=1_000_000)
        receipt = self.spool.enqueue(env)
        self.assertTrue(receipt["enqueued"])
        self.assertTrue((self.spool.outbox_dir / f"{env.id}.json").exists())
        queue = self.spool.all_messages()
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0].delivery_state, "QUEUED")

    def test_dedup_rejects_second_enqueue(self):
        env = LoraEnvelope("ALARM: poziom wody", now_ms=1_000_000)
        self.assertTrue(self.spool.enqueue(env)["enqueued"])
        duplicate = LoraEnvelope("ALARM: poziom wody", now_ms=2_000_000)
        receipt = self.spool.enqueue(duplicate)
        self.assertFalse(receipt["enqueued"])
        self.assertEqual(receipt["reason"], "duplicate_dedup_hash")
        self.assertEqual(len(self.spool.all_messages()), 1)

    def test_expired_message_never_enters_outbox(self):
        env = LoraEnvelope("stara wiadomosc", ttl_minutes=1, now_ms=1_000_000)
        receipt = self.spool.enqueue(env, now_ms=1_000_000 + 5 * 60 * 1000)
        self.assertFalse(receipt["enqueued"])
        self.assertEqual(receipt["reason"], "expired")
        self.assertEqual(self.spool.all_messages()[0].delivery_state, "EXPIRED")

    def test_mark_state_and_pending(self):
        env = LoraEnvelope("x", now_ms=1_000_000)
        self.spool.enqueue(env)
        self.spool.mark_state(env.id, "DELIVERED")
        self.assertEqual(self.spool.pending(), [])
        self.assertEqual(self.spool.all_messages()[0].delivery_state, "DELIVERED")

    def test_expire_old_messages_sweeps_queue(self):
        env = LoraEnvelope("x", ttl_minutes=1, now_ms=1_000_000)
        self.spool.enqueue(env)
        swept = self.spool.expire_old_messages(now_ms=1_000_000 + 10 * 60 * 1000)
        self.assertEqual(swept, 1)
        self.assertEqual(self.spool.all_messages()[0].delivery_state, "EXPIRED")

    def test_tx_plan_prioritizes_p0_and_respects_window(self):
        for i in range(3):
            self.spool.enqueue(LoraEnvelope(f"tech nr {i}", priority=P2_TECHNICAL, now_ms=1_000_000))
        self.spool.enqueue(LoraEnvelope("SOS z pola", priority=P0_CRITICAL, now_ms=1_000_000))
        plan = self.spool.tx_plan(tx_window_s=5.0)
        self.assertGreater(plan["messages_in_window"], 0)
        self.assertEqual(plan["plan"][0]["priority"], P0_CRITICAL)
        self.assertLessEqual(plan["planned_airtime_s"], plan["usable_airtime_s"])


class AdvisoryFormatTest(unittest.TestCase):
    def test_hub_tag_and_edge_tag(self):
        hub = format_advisory_for_edge("temp poza pasmem")
        self.assertIn("[HUB→EDGE]", hub)
        edge = format_advisory_for_edge("temp poza pasmem", origin_network="MESHTASTIC")
        self.assertIn("[EDGE→HUB]", edge)

    def test_sanitize_strips_control_chars(self):
        dirty = "tekst\x00\x1fz\x07kontrolnymi"
        cleaned = sanitize_for_radio(dirty)
        for ch in cleaned:
            self.assertNotIn(ch, "\x00\x07\x1f")


if __name__ == "__main__":
    unittest.main()
