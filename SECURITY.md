# Security

This project observes unencrypted MQTT traffic that may contain credentials and
unique identifiers. Public reports must never include packet captures, complete
logs, credentials, MAC addresses, datalogger identifiers, or complete MQTT
topics.

To report a vulnerability, do not open a public issue containing real device
data. Use the repository's private security reporting channel once available.

The bridge injects only the explicitly allow-listed Modbus read for telemetry
block `0x1195`. Its private request envelope is stored in `/data`, the app's
private persistent storage, with restricted permissions. This file may be
included in app backups, so backups must be protected as private data.

The bridge never writes inverter registers. Any future control feature must be
optional, restricted by an explicit register allow-list, and covered by tests.

The ESPHome component stores no identifier in source control, but its private
`dtu_id` secret is used at compile time to derive the local Bluetooth protocol
key. Treat `secrets.yaml`, ESPHome build directories, diagnostic bundles and
compiled firmware images as sensitive. Public issues should contain only
sanitized log lines and must omit Bluetooth addresses and telemetry values.
