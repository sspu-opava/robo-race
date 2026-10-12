import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "controllers" / "roborace_controller"))

from protocol import decode_message, encode_message


class ProtocolTests(unittest.TestCase):
    def test_decode_and_encode_json_messages(self):
        message, error = decode_message('{"type":"validate","request_id":"a1","source":"PLYN(5)"}')
        self.assertIsNone(error)
        self.assertEqual(message["source"], "PLYN(5)")
        self.assertEqual(json.loads(encode_message(message)), message)

    def test_rejects_invalid_shapes_types_and_ids(self):
        for raw in ["not-json", "[]", '{"type":"launch"}', '{"type":"start","request_id":12}']:
            with self.subTest(raw=raw):
                message, error = decode_message(raw)
                self.assertIsNone(message)
                self.assertIsNotNone(error)

    def test_czech_text_survives_webots_character_count(self):
        payload = {"type": "ready", "message": "Příliš rychlá zatáčka: kužel, žebříček.",
                   "sample_program": "# Ověřená jízda\nPLYN(45)"}
        wire = encode_message(payload)
        self.assertTrue(wire.isascii())
        # Reproduce the R2025a Python binding's len(text) byte count.
        self.assertEqual(json.loads(wire.encode("utf-8")[:len(wire)]), payload)

    def test_handshake_and_view_restore_are_recognized(self):
        for kind in ("hello", "restore_view"):
            message, error = decode_message(json.dumps({"type": kind}))
            self.assertIsNone(error)
            self.assertEqual(message["type"], kind)


if __name__ == "__main__":
    unittest.main()
