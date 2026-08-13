import base64
import json
import time
import tempfile
import unittest
from pathlib import Path

from easun_bridge.easun_bridge import (
    MQTTStreamParser,
    TelemetryObserver,
    ReadRequestTemplate,
    decode_publish,
    encode_remaining_length,
    extract_modbus_frames,
    modbus_frame_paths,
    read_request_template,
    safe_payload_shape,
    payload_scalar_map,
    safe_scalar_changes,
    modbus_crc,
    response_words_little_endian,
    safe_topic,
)


def with_crc(data: bytes) -> bytes:
    return data + modbus_crc(data).to_bytes(2, "little")


def publish(topic: str, payload: bytes) -> bytes:
    body = len(topic.encode()).to_bytes(2, "big") + topic.encode() + payload
    return b"\x30" + encode_remaining_length(len(body)) + body


class BridgeTests(unittest.TestCase):
    def test_stream_reassembly(self):
        packets = []
        parser = MQTTStreamParser(packets.append)
        first = publish("a/b", b"one")
        second = publish("a/b", b"two")
        parser.feed((first + second)[:5])
        self.assertEqual([], packets)
        parser.feed((first + second)[5:])
        self.assertEqual([first, second], packets)

    def test_publish_decode(self):
        packet = publish("dtu/device/pub/test", b'{"ok":true}')
        self.assertEqual(("dtu/device/pub/test", b'{"ok":true}'), decode_publish(packet))

    def test_modbus_json_decode(self):
        frame = with_crc(bytes.fromhex("05 03 04 03 00 07 09"))
        payload = json.dumps({"b": {"ct": [{"co": base64.b64encode(frame).decode()}]}}).encode()
        self.assertEqual([frame], extract_modbus_frames(payload))
        self.assertEqual([3, 2311], response_words_little_endian(frame))

    def test_rwb1_nul_prefixed_json(self):
        frame = with_crc(bytes.fromhex("05 03 02 03 00"))
        payload = b"\x00" + json.dumps({"b": {"co": base64.b64encode(frame).decode()}}).encode()
        self.assertEqual([frame], extract_modbus_frames(payload))
        self.assertEqual((True, ["b.co"]), modbus_frame_paths(payload))

    def test_safe_envelope_reports_only_frame_paths(self):
        frame = with_crc(bytes.fromhex("05 03 11 B7 00 01"))
        payload = json.dumps(
            {
                "device_identifier_that_must_not_be_logged": "private-value",
                "b": {"ci": base64.b64encode(frame).decode()},
            }
        ).encode()
        nul_prefixed, paths = modbus_frame_paths(payload)
        self.assertFalse(nul_prefixed)
        self.assertEqual(["b.ci"], paths)

    def test_safe_shape_never_contains_values(self):
        payload = json.dumps(
            {"private_identifier": "must-not-appear", "b": {"ci": "secret-frame"}}
        ).encode()
        shape = safe_payload_shape(payload)
        self.assertIn("private_identifier=string(15)", shape)
        self.assertIn("b.ci=string(12)", shape)
        self.assertNotIn("must-not-appear", shape)
        self.assertNotIn("secret-frame", shape)

    def test_safe_comparison_reports_only_change_metadata(self):
        previous = payload_scalar_map(b'{"i":100,"s":"123456789","t":"11:00:01","b":{"ci":"one","no":4}}')
        current = payload_scalar_map(b'{"i":101,"s":"123456799","t":"11:00:06","b":{"ci":"two","no":4}}')
        comparison = safe_scalar_changes(previous, current)
        self.assertIn("i=numeric-delta(+1)", comparison)
        self.assertIn("s=digit-string-delta(+10)", comparison)
        self.assertIn("t=clock-HH:MM:SS-delta(+5s)", comparison)
        self.assertIn("b.no", comparison)
        self.assertNotIn("123456789", comparison)
        self.assertNotIn("123456799", comparison)

    def test_bad_crc_is_rejected(self):
        frame = bytes.fromhex("05 03 02 01 00 00 00")
        payload = json.dumps({"b": {"co": base64.b64encode(frame).decode()}}).encode()
        self.assertEqual([], extract_modbus_frames(payload))

    def test_confirmed_telemetry_block(self):
        words = [
            3, 2311, 500, 0, 0, 261, 47, 0, 22, 2292, 500,
            595, 462, 15, 15, 0, 220, 15302, 0, 1, 4200,
        ]
        data = b"".join(value.to_bytes(2, "little") for value in words)
        frame = with_crc(bytes((5, 3, len(data))) + data)
        observer = TelemetryObserver()

        observer._observe_frame("downstream", frame)

        self.assertEqual(231.1, observer.latest_state["grid_voltage"])
        self.assertEqual(26.1, observer.latest_state["battery_voltage"])
        self.assertEqual(595, observer.latest_state["load_apparent_power"])
        self.assertEqual(462, observer.latest_state["load_power"])
        self.assertEqual(4200, observer.latest_state["rated_power"])

    def test_device_topic_is_redacted(self):
        topic = "dtu/123456789012345678901234/pub/event/123456789012345"
        self.assertEqual("dtu/[device]/pub/event/[device]", safe_topic(topic))

    def test_read_request_is_correlated_with_response(self):
        observer = TelemetryObserver()
        request = with_crc(bytes.fromhex("05 03 11 B7 00 01"))
        response = with_crc(bytes.fromhex("05 03 02 71 04"))

        observer._observe_frame("upstream", request)
        self.assertEqual(1, len(observer.pending_reads))
        observer._observe_frame("downstream", response)
        self.assertEqual(0, len(observer.pending_reads))

    def test_allowlisted_read_packet_uses_captured_envelope(self):
        original = with_crc(bytes.fromhex("05 03 11 D1 00 01"))
        payload = b"\x00" + json.dumps(
            {
                "t": "Ab3xYz90",
                "s": "9aBcD2eF7",
                "request": "kept-in-memory",
                "b": {"ci": base64.b64encode(original).decode()},
            }
        ).encode()
        template = read_request_template(publish("dtu/private/sub/service/dev_rpc", payload))
        self.assertIsNotNone(template)
        generated = template.packet_for(0x1195, 21)
        topic, generated_payload = decode_publish(generated)
        self.assertEqual("dtu/private/sub/service/dev_rpc", topic)
        self.assertEqual(
            [with_crc(bytes.fromhex("05 03 11 95 00 15"))],
            extract_modbus_frames(generated_payload),
        )
        generated_document = json.loads(generated_payload.lstrip(b"\x00"))
        self.assertRegex(generated_document["t"], r"[A-Z][a-z]\d[a-z][A-Z][a-z]\d\d")
        self.assertRegex(generated_document["s"], r"\d[a-z][A-Z][a-z][A-Z]\d[a-z][A-Z]\d")
        self.assertNotEqual("Ab3xYz90", generated_document["t"])
        self.assertNotEqual("9aBcD2eF7", generated_document["s"])

    def test_arbitrary_active_read_is_rejected(self):
        original = with_crc(bytes.fromhex("05 03 11 D1 00 01"))
        payload = json.dumps({"b": {"ci": base64.b64encode(original).decode()}}).encode()
        template = read_request_template(publish("safe/topic", payload))
        with self.assertRaises(ValueError):
            template.packet_for(0x138C, 1)

    def test_pending_cloud_read_blocks_local_poll(self):
        observer = TelemetryObserver()
        observer.pending_reads.append((0x11D1, 1, time.monotonic(), False))
        self.assertTrue(observer.has_pending_read())

    def test_expired_read_does_not_block_local_poll(self):
        observer = TelemetryObserver()
        observer.pending_reads.append((0x11D1, 1, time.monotonic() - 11, False))
        self.assertFalse(observer.has_pending_read())

    def test_private_template_cache_round_trip(self):
        original = with_crc(bytes.fromhex("05 03 11 D1 00 01"))
        payload = json.dumps({"b": {"ci": base64.b64encode(original).decode()}}).encode()
        template = read_request_template(publish("safe/topic", payload))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "template.json"
            template.save(path)
            loaded = ReadRequestTemplate.load(path)
        self.assertEqual(template.topic, loaded.topic)
        self.assertEqual(template.document, loaded.document)


if __name__ == "__main__":
    unittest.main()
