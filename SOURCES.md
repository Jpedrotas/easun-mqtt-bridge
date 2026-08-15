# Sources and evidence

This document records the sources used to design, implement, and document EASUN
MQTT Bridge. Sources are grouped by authority. A reference project can support a
compatibility hypothesis but does not by itself prove compatibility with the
tested inverter.

Links and upstream repository revisions were checked on 2026-08-15.

## Standards and official protocol documentation

| Source | Used for |
|---|---|
| [OASIS MQTT Version 3.1.1](https://www.oasis-open.org/standard/mqttv3-1-1/) | MQTT packet structure and protocol behavior |
| [Modbus protocol specifications](https://www.modbus.org/modbus-specifications) | Modbus function-code semantics |
| [Modbus Serial Line Protocol and Implementation Guide V1.02](https://modbus.org/docs/Modbus_over_serial_line_V1_02.pdf) | RTU framing, byte transport, and CRC behavior |

## Home Assistant documentation

| Source | Used for |
|---|---|
| [App configuration](https://developers.home-assistant.io/docs/apps/configuration/) | `config.yaml`, `/data` persistent storage, ports, services, architecture, and app metadata |
| [Create an app repository](https://developers.home-assistant.io/docs/apps/repository/) | `repository.yaml` and repository installation flow |
| [Publishing an app](https://developers.home-assistant.io/docs/apps/publishing/) | Current app publishing and image guidance |
| [Official Mosquitto Broker app documentation](https://github.com/home-assistant/addons/blob/master/mosquitto/DOCS.md) | Mosquitto installation and Home Assistant MQTT service expectations |
| [Home Assistant example app repository](https://github.com/home-assistant/addons-example) | Repository and app directory structure |

Installed Home Assistant, OS, Supervisor, kernel, architecture, and Mosquitto app
versions in the compatibility matrix were queried directly from the private test
system. No configuration export, token, credential, or diagnostic bundle is
included in this repository.

## ESPHome documentation

| Source | Used for |
|---|---|
| [External Components](https://esphome.io/components/external_components/) | Loading the public `rwb1_ble` component from this repository |
| [ESP32 Bluetooth Low Energy Tracker](https://esphome.io/components/esp32_ble_tracker/) | BLE scanning and ESP32 resource considerations |
| [ESP32 Bluetooth Low Energy Client](https://esphome.io/components/esp32_ble_client/) | Persistent GATT client lifecycle and notifications/indications |

## OpenWrt documentation

| Source | Used for |
|---|---|
| [OpenWrt firewall configuration](https://openwrt.org/docs/guide-user/firewall/firewall_configuration) | firewall4/UCI redirect fields, DNAT, SNAT, reload, validation, and backup guidance |
| [OpenWrt firewall NAT examples](https://openwrt.org/docs/guide-user/firewall/fw3_configurations/fw3_nat) | NAT and masquerade behavior across firewall generations |

The original Archer C20 configuration showed firewall3 and
`/etc/firewall.user`; the public installer instead targets firewall4 and checks
for `fw4` before making changes. The exact original OpenWrt point release was not
preserved and is therefore not claimed.

## Hardware and vendor sources

| Source | Used for |
|---|---|
| [TP-Link Archer C20 v5 support downloads](https://www.tp-link.com/en/support/download/archer-c20/v5/) | Router hardware-revision awareness and vendor firmware provenance |
| EASUN SMH III manual supplied with the test equipment | Inverter rating and operational context; the local PDF is not redistributed here |
| Physical labels on the inverter, RWB1, and packaging | Model, type, and commercial reference; serial number, device ID, MAC address, and QR code are deliberately omitted |

A downloaded firmware image is recorded only as an available candidate package.
It is never presented as installed unless the active device reports that exact
version.

## Interoperability references

These projects helped identify protocol families and candidate registers. Their
licenses and implementations remain separate; no source code was copied into
this bridge.

| Source | Revision used | Contribution to the investigation |
|---|---|---|
| [samuelolteanu/Local-Cloud-Bridge-for-Anenji-Easun-MPP-Solar-Inverters](https://github.com/samuelolteanu/Local-Cloud-Bridge-for-Anenji-Easun-MPP-Solar-Inverters/tree/34f5abe1afec820175a135daa0fe79b3b739c902) | `34f5abe1` | Initial local-cloud interception architecture and one-second polling concept for related hardware |
| [odya/esphome-powmr-hybrid-inverter](https://github.com/odya/esphome-powmr-hybrid-inverter/tree/cd841713c0a7c9c90b90ac897e2c5268f0775ea4) | `cd841713` | PowMr register batches, little-endian interpretation, and related settings |
| [leodesigner/powmr_comm](https://github.com/leodesigner/powmr_comm/tree/7b6013a9f52fbb2e9631fe641bb2b241751c08cb) | `7b6013a9` | Independent occurrence of the `0x1399` request and CRC bytes |
| [SolarAssistant EASUN/Sumry documentation](https://solar-assistant.io/help/inverters/easun/ISolar-SMG-III/eybond-sumry) | Web documentation | Evidence that related EASUN SMH/SMG III devices use the Sumry protocol family |

## Primary evidence from the tested equipment

The final register assignments, response byte order, MQTT envelope behavior,
request correlation, BLE framing/cryptography and active-polling behavior were
validated against private captures and live observations from the exact test
system. Direct ESP32-C3 BLE polling was validated at two-second cadence with CRC
checking. This primary evidence has greater weight for this project than
similarity to external register maps.

For privacy and security, the repository does **not** contain:

- packet captures;
- complete MQTT topics or payloads;
- credentials or authentication fields;
- serial numbers, device IDs, MAC addresses, or QR codes;
- private IP addresses or a complete site configuration.

Sanitized tests contain only synthetic envelopes and the minimum protocol bytes
needed to verify decoding, CRC checks, allow-list enforcement, and request
correlation.

## Evidence policy

- **Confirmed** means observed on the exact test equipment or stated by an
  authoritative standard/vendor source.
- **Inferred** means supported by archived configuration or several independent
  compatibility references but not directly reported by the active device.
- **Unknown** means the version or revision was not exposed or preserved.
- Community projects are cited as interoperability references, never as proof
  that every related inverter or firmware is compatible.
