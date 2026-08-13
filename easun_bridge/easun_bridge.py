#!/usr/bin/env python3
"""Transparent MQTT proxy and passive EASUN telemetry decoder.

The datalogger connection is forwarded byte-for-byte to the vendor broker.  The
observer never logs MQTT credentials or the device-specific part of a topic.
Only read-only telemetry is decoded; this version does not inject commands.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import logging
import os
import signal
import struct
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


LOGGER = logging.getLogger("easun_bridge")
MAX_MQTT_PACKET = 1024 * 1024


def encode_remaining_length(value: int) -> bytes:
    encoded = bytearray()
    while True:
        digit = value % 128
        value //= 128
        if value:
            digit |= 0x80
        encoded.append(digit)
        if not value:
            return bytes(encoded)


def decode_remaining_length(data: bytes | bytearray, offset: int = 1) -> tuple[int, int] | None:
    value = 0
    multiplier = 1
    for position in range(offset, min(len(data), offset + 4)):
        digit = data[position]
        value += (digit & 0x7F) * multiplier
        if not digit & 0x80:
            return value, position + 1
        multiplier *= 128
    return None


class MQTTStreamParser:
    """Reassemble complete MQTT packets from arbitrary TCP chunks."""

    def __init__(self, callback: Callable[[bytes], None]) -> None:
        self._buffer = bytearray()
        self._callback = callback

    def feed(self, chunk: bytes) -> None:
        self._buffer.extend(chunk)
        while len(self._buffer) >= 2:
            decoded = decode_remaining_length(self._buffer)
            if decoded is None:
                if len(self._buffer) > 5:
                    raise ValueError("invalid MQTT remaining length")
                return
            remaining, variable_header = decoded
            if remaining > MAX_MQTT_PACKET:
                raise ValueError("MQTT packet exceeds safety limit")
            total = variable_header + remaining
            if len(self._buffer) < total:
                return
            packet = bytes(self._buffer[:total])
            del self._buffer[:total]
            self._callback(packet)


def modbus_crc(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


def decode_publish(packet: bytes) -> tuple[str, bytes] | None:
    if not packet or packet[0] >> 4 != 3:
        return None
    decoded = decode_remaining_length(packet)
    if decoded is None:
        return None
    _, position = decoded
    if position + 2 > len(packet):
        return None
    topic_length = int.from_bytes(packet[position : position + 2], "big")
    position += 2
    if position + topic_length > len(packet):
        return None
    topic = packet[position : position + topic_length].decode("utf-8", "replace")
    position += topic_length
    qos = (packet[0] >> 1) & 0x03
    if qos:
        position += 2
    return topic, packet[position:]


def safe_topic(topic: str) -> str:
    parts = topic.split("/")
    return "/".join("[device]" if len(part) > 8 else part for part in parts)


def extract_modbus_frames(payload: bytes) -> list[bytes]:
    # RWB1 prefixes its JSON application payload with a NUL byte even on QoS 0
    # PUBLISH packets.  This is vendor-specific and not an MQTT packet id.
    payload = payload.lstrip(b"\x00")
    try:
        document = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return []
    container = document.get("b")
    if not isinstance(container, dict):
        return []
    encoded: list[str] = []
    for key in ("ci", "co"):
        if isinstance(container.get(key), str):
            encoded.append(container[key])
            break
    reports = container.get("ct")
    if isinstance(reports, list):
        for report in reports:
            if isinstance(report, dict) and isinstance(report.get("co"), str):
                encoded.append(report["co"])
    frames = []
    for item in encoded:
        try:
            frame = base64.b64decode(item, validate=True)
        except (ValueError, TypeError):
            continue
        if len(frame) >= 4 and modbus_crc(frame[:-2]) == int.from_bytes(frame[-2:], "little"):
            frames.append(frame)
    return frames


def response_words_little_endian(frame: bytes) -> list[int] | None:
    if len(frame) < 5 or frame[1] != 3:
        return None
    byte_count = frame[2]
    data = frame[3 : 3 + byte_count]
    if len(data) != byte_count or byte_count % 2:
        return None
    return [int.from_bytes(data[index : index + 2], "little") for index in range(0, len(data), 2)]


@dataclass(frozen=True)
class SensorDefinition:
    key: str
    name: str
    unit: str | None
    device_class: str | None
    state_class: str | None


SENSORS = (
    SensorDefinition("status_code", "Estado (código)", None, None, None),
    SensorDefinition("grid_voltage", "Tensão da rede", "V", "voltage", "measurement"),
    SensorDefinition("grid_frequency", "Frequência da rede", "Hz", "frequency", "measurement"),
    SensorDefinition("pv_voltage", "Tensão fotovoltaica", "V", "voltage", "measurement"),
    SensorDefinition("pv_power", "Potência fotovoltaica", "W", "power", "measurement"),
    SensorDefinition("battery_voltage", "Tensão da bateria", "V", "voltage", "measurement"),
    SensorDefinition("battery_soc", "Carga da bateria", "%", "battery", "measurement"),
    SensorDefinition("battery_charge_current", "Corrente de carga da bateria", "A", "current", "measurement"),
    SensorDefinition("battery_discharge_current", "Corrente de descarga da bateria", "A", "current", "measurement"),
    SensorDefinition("output_voltage", "Tensão de saída", "V", "voltage", "measurement"),
    SensorDefinition("output_frequency", "Frequência de saída", "Hz", "frequency", "measurement"),
    SensorDefinition("load_apparent_power", "Potência aparente da carga", "VA", "apparent_power", "measurement"),
    SensorDefinition("load_power", "Potência ativa da carga", "W", "power", "measurement"),
    SensorDefinition("load_percent", "Carga do inversor", "%", None, "measurement"),
    SensorDefinition("rated_power", "Potência nominal", "W", "power", "measurement"),
    SensorDefinition("last_telemetry", "Última telemetria", None, "timestamp", None),
)


class LocalMQTTPublisher:
    """Small MQTT 3.1.1 publisher used for HA Discovery and state."""

    def __init__(self, host: str, port: int, username: str | None, password: str | None) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()

    @staticmethod
    def _field(value: bytes) -> bytes:
        return len(value).to_bytes(2, "big") + value

    async def connect(self) -> None:
        if self.writer and not self.writer.is_closing():
            return
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        client_id = f"easun-ha-bridge-{os.getpid()}".encode()
        # Clean session plus a retained Last Will. Home Assistant can therefore
        # mark the entities unavailable if the bridge or host disappears.
        flags = 0x02 | 0x04 | 0x20
        payload = self._field(client_id)
        payload += self._field(b"easun/bridge/availability")
        payload += self._field(b"offline")
        if self.username is not None:
            flags |= 0x80
            payload += self._field(self.username.encode())
        if self.password is not None:
            flags |= 0x40
            payload += self._field(self.password.encode())
        # Keepalive 0 is intentional. Telemetry may arrive only every five
        # minutes, so a short MQTT keepalive would make the broker close this
        # tiny write-only client between updates.
        variable = self._field(b"MQTT") + bytes((4, flags)) + struct.pack("!H", 0)
        body = variable + payload
        self.writer.write(b"\x10" + encode_remaining_length(len(body)) + body)
        await self.writer.drain()
        reply = await asyncio.wait_for(self.reader.readexactly(4), timeout=5)
        if reply[:3] != b"\x20\x02\x00" or reply[3] != 0:
            await self.close()
            raise ConnectionError(f"local MQTT broker rejected connection (code {reply[3] if len(reply) > 3 else -1})")
        await self.publish_discovery()
        await self._publish_connected(
            "easun/bridge/availability", b"online", retain=True
        )

    async def close(self) -> None:
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        self.reader = None
        self.writer = None

    async def publish(self, topic: str, payload: bytes, retain: bool = False) -> None:
        async with self._lock:
            await self.connect()
            await self._publish_connected(topic, payload, retain)

    async def _publish_connected(self, topic: str, payload: bytes, retain: bool = False) -> None:
        """Publish while already connected; the caller handles locking."""
        assert self.writer is not None
        topic_bytes = topic.encode()
        body = self._field(topic_bytes) + payload
        header = 0x31 if retain else 0x30
        self.writer.write(bytes((header,)) + encode_remaining_length(len(body)) + body)
        await self.writer.drain()

    async def publish_discovery(self) -> None:
        # Called after the connection is established, so write directly to avoid
        # recursively acquiring the publish lock.
        assert self.writer is not None
        for sensor in SENSORS:
            config: dict[str, Any] = {
                "name": sensor.name,
                "unique_id": f"easun_bridge_{sensor.key}",
                "state_topic": "easun/bridge/state",
                "availability_topic": "easun/bridge/availability",
                "value_template": "{{ value_json.%s }}" % sensor.key,
                "origin": {
                    "name": "EASUN MQTT Bridge",
                    "sw_version": "0.1.0",
                },
                "device": {
                    "identifiers": ["easun_mqtt_bridge"],
                    "name": "EASUN MQTT Bridge",
                    "manufacturer": "EASUN",
                    "model": "SMH III via RWB1",
                },
            }
            if sensor.unit:
                config["unit_of_measurement"] = sensor.unit
            if sensor.device_class:
                config["device_class"] = sensor.device_class
            if sensor.state_class:
                config["state_class"] = sensor.state_class
            topic = f"homeassistant/sensor/easun_bridge/{sensor.key}/config".encode()
            body = self._field(topic) + json.dumps(config, separators=(",", ":")).encode()
            self.writer.write(b"\x31" + encode_remaining_length(len(body)) + body)
        await self.writer.drain()


class TelemetryObserver:
    def __init__(self, local_publisher: LocalMQTTPublisher | None = None) -> None:
        self.local_publisher = local_publisher
        self.latest_state: dict[str, Any] = {}
        self.pending_reads: deque[tuple[int, int, float]] = deque(maxlen=32)

    def packet(self, direction: str, packet: bytes) -> None:
        packet_type = packet[0] >> 4
        if packet_type == 1:
            LOGGER.info("MQTT CONNECT observed (%s); credentials intentionally hidden", direction)
            return
        decoded = decode_publish(packet)
        if decoded is None:
            return
        topic, payload = decoded
        frames = extract_modbus_frames(payload)
        if not frames:
            return
        LOGGER.info("MQTT %s: %d valid Modbus frame(s) on %s", direction, len(frames), safe_topic(topic))
        for frame in frames:
            self._observe_frame(direction, frame)

    def _observe_frame(self, direction: str, frame: bytes) -> None:
        function = frame[1]
        if function == 3 and direction == "downstream":
            words = response_words_little_endian(frame)
            if words is None:
                return
            correlated_register = self._match_pending_read(len(words))
            if correlated_register is None:
                LOGGER.info("Telemetry block received: %d words", len(words))
            else:
                LOGGER.info(
                    "Modbus read response: register=0x%04X words=%s",
                    correlated_register,
                    words,
                )
            if len(words) == 21:
                self.latest_state.update(
                    {
                        "status_code": words[0],
                        "grid_voltage": words[1] / 10,
                        "grid_frequency": words[2] / 10,
                        "pv_voltage": words[3] / 10,
                        "pv_power": words[4],
                        "battery_voltage": words[5] / 10,
                        "battery_soc": words[6],
                        "battery_charge_current": words[7],
                        "battery_discharge_current": words[8],
                        "output_voltage": words[9] / 10,
                        "output_frequency": words[10] / 10,
                        # This firmware reports the physically consistent pair
                        # as apparent power first and active power second.
                        "load_apparent_power": words[11],
                        "load_power": words[12],
                        "load_percent": words[13],
                        "rated_power": words[20],
                        "last_telemetry": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    }
                )
                if self.local_publisher:
                    asyncio.create_task(
                        self.local_publisher.publish(
                            "easun/bridge/state",
                            json.dumps(self.latest_state, separators=(",", ":")).encode(),
                            retain=True,
                        )
                    )
        elif function in (3, 6) and len(frame) >= 8:
            register = int.from_bytes(frame[2:4], "big")
            value = int.from_bytes(frame[4:6], "big")
            operation = "read" if function == 3 else "write"
            LOGGER.info("Modbus %s request: register=0x%04X value=%d", operation, register, value)
            if function == 3 and direction == "upstream":
                self.pending_reads.append((register, value, time.monotonic()))

    def _match_pending_read(self, word_count: int) -> int | None:
        now = time.monotonic()
        while self.pending_reads and now - self.pending_reads[0][2] > 10:
            self.pending_reads.popleft()
        if not self.pending_reads:
            return None
        register, expected_words, _ = self.pending_reads[0]
        if expected_words != word_count:
            return None
        self.pending_reads.popleft()
        return register


async def relay(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    parser: MQTTStreamParser,
) -> None:
    try:
        while data := await reader.read(65536):
            parser.feed(data)
            writer.write(data)
            await writer.drain()
    finally:
        if not writer.is_closing():
            writer.close()


async def handle_client(
    downstream_reader: asyncio.StreamReader,
    downstream_writer: asyncio.StreamWriter,
    upstream_host: str,
    upstream_port: int,
    observer: TelemetryObserver,
) -> None:
    peer = downstream_writer.get_extra_info("peername")
    LOGGER.info("Datalogger connection accepted from %s", peer[0] if peer else "unknown")
    try:
        upstream_reader, upstream_writer = await asyncio.open_connection(upstream_host, upstream_port)
    except Exception:
        LOGGER.exception("Could not connect to upstream MQTT broker")
        downstream_writer.close()
        await downstream_writer.wait_closed()
        return
    down_parser = MQTTStreamParser(lambda packet: observer.packet("downstream", packet))
    up_parser = MQTTStreamParser(lambda packet: observer.packet("upstream", packet))
    tasks = {
        asyncio.create_task(relay(downstream_reader, upstream_writer, down_parser)),
        asyncio.create_task(relay(upstream_reader, downstream_writer, up_parser)),
    }
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    for task in pending:
        task.cancel()
    await asyncio.gather(*done, *pending, return_exceptions=True)
    upstream_writer.close()
    downstream_writer.close()
    await asyncio.gather(upstream_writer.wait_closed(), downstream_writer.wait_closed(), return_exceptions=True)
    LOGGER.info("Datalogger connection closed")


async def run(args: argparse.Namespace) -> None:
    local_publisher = None
    if args.local_mqtt_host:
        local_publisher = LocalMQTTPublisher(
            args.local_mqtt_host,
            args.local_mqtt_port,
            os.getenv("EASUN_LOCAL_MQTT_USERNAME"),
            os.getenv("EASUN_LOCAL_MQTT_PASSWORD"),
        )
        await local_publisher.connect()
        LOGGER.info("Connected to local MQTT broker")
    observer = TelemetryObserver(local_publisher)
    server = await asyncio.start_server(
        lambda reader, writer: handle_client(
            reader, writer, args.upstream_host, args.upstream_port, observer
        ),
        args.listen_host,
        args.listen_port,
    )
    addresses = ", ".join(str(sock.getsockname()) for sock in server.sockets or [])
    LOGGER.info("Safe passive proxy listening on %s", addresses)
    try:
        async with server:
            await server.serve_forever()
    finally:
        if local_publisher:
            await local_publisher.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--listen-host", default="0.0.0.0")
    parser.add_argument("--listen-port", type=int, default=18830)
    parser.add_argument(
        "--upstream-host",
        required=True,
        help="vendor MQTT broker hostname or address observed on the router",
    )
    parser.add_argument("--upstream-port", type=int, default=1883)
    parser.add_argument("--local-mqtt-host")
    parser.add_argument("--local-mqtt-port", type=int, default=1883)
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    if os.name != "nt":
        signal.signal(signal.SIGTERM, lambda *_: raise_cancelled())
    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:
        pass


def raise_cancelled() -> None:
    raise KeyboardInterrupt


if __name__ == "__main__":
    main()
