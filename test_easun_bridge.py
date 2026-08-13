import base64
import json
import unittest

from easun_bridge.easun_bridge import (
    MQTTStreamParser,
    TelemetryObserver,
    decode_publish,
    encode_remaining_length,
    extract_modbus_frames,
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


if __name__ == "__main__":
    unittest.main()
