# Changelog

All notable changes to this project are documented in this file.

## [0.4.1] - 2026-08-15

- Reduced the production ESP32-C3 BLE scan duty cycle to allow reliable Wi-Fi
  authentication on mesh and multi-access-point networks while retaining
  automatic RWB1 discovery.
- Documented ESP32-C3 Wi-Fi/Bluetooth radio coexistence behavior.

## [0.4.0] - 2026-08-15

- Added a read-only ESPHome external component for direct RWB1 Bluetooth LE
  telemetry on ESP32-C3, with automatic `SSL_` discovery and no fixed MAC.
- Added all 15 confirmed telemetry sensors, CRC validation and a configurable
  activity LED that blinks on communication.
- Validated repeated two-second polling on the confirmed hardware using ESPHome
  2026.7.4 and ESP-IDF 5.5.5.
- Added a public configuration, secrets template, diagnostic build and privacy
  guidance. No device-specific capture, address, identifier or key is included.
- Documented how to copy the DTU ID from the vendor application's Device
  Information page and distinguish it from the SN, BLE name and MAC.
- Standardized the new ESPHome component, firmware logs, CLI tools and public
  documentation in English for international use.
- Added a clear notice that this is an unofficial community project with no
  vendor affiliation or endorsement.

## [0.3.3] - 2026-08-13

- Clarified intentional IPv4 octet splitting in the OpenWrt helper and made
  zone-name expansion unambiguous for ShellCheck portability validation.

## [0.3.2] - 2026-08-13

- Replaced the obsolete Home Assistant app watchdog option with a native
  Docker health check for the local proxy listener.
- Removed an explicit default configuration key rejected by the current Home
  Assistant app linter.
- Corrected shell variable assignment/export handling reported by ShellCheck.

## [0.3.1] - 2026-08-13

- Added local read-only polling of the confirmed `0x1195` telemetry block every
  two seconds, with request serialization and suppression of local responses
  before cloud forwarding.
- Stored the private protocol envelope in `/data`, the app's private persistent
  storage, with restricted permissions. It is never committed or logged.
- Added `poll_interval`; setting it to `0` disables local polling.
- Rate-limited periodic health messages to reduce unnecessary storage writes.
- Added a complete Home Assistant and OpenWrt installation guide, a reversible
  firewall4/UCI helper, version-difference notes, rollback steps, and a
  troubleshooting matrix.
- Added a hardware/software/firmware inventory and compatibility matrix that
  distinguishes confirmed, inferred, unknown, and replacement-router versions.
- Added a traceable source catalogue covering standards, official Home Assistant
  and OpenWrt documentation, hardware references, pinned interoperability
  project revisions, and the private-evidence policy.

## [0.2.1] - 2026-08-12

### Changed

- Added safe structural diagnostics for the MQTT envelope without logging
  content, identifiers, or credentials.
- Confirmed that cloud requests contain two varying alphanumeric values. An
  initial local-read experiment was rejected by the RWB1, so the experimental
  option was removed until the envelope behavior was understood.

## [0.1.0] - 2026-08-12

### Added

- Transparent passive MQTT proxy for the Solar Plug-RWB1 datalogger.
- Decoding of confirmed Modbus RTU blocks and Home Assistant MQTT Discovery.
- Home Assistant OS app with automatic Mosquitto service integration.
- Register map with confidence levels and a compatibility matrix.
- Unit tests, syntax validation, and continuous integration.

### Security

- Datalogger MQTT credentials were never logged.
- Device-specific identifiers were redacted from logged MQTT topics.
- This version did not inject requests or implement Modbus writes.
