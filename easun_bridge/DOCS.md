# EASUN MQTT Bridge

This app runs a transparent MQTT proxy for the EASUN Solar Plug-RWB1
datalogger. It forwards the original connection to the vendor cloud and
publishes confirmed telemetry to local Mosquitto using Home Assistant MQTT
Discovery. It can also poll the confirmed telemetry block locally in read-only
mode.

## Before starting

1. Install and start the official Mosquitto Broker app.
2. Confirm that the Home Assistant MQTT integration is active.
3. Determine the MQTT broker address used by the datalogger from a router
   capture. Never publish that capture or any credentials it contains.

## Options

- `upstream_host`: vendor cloud MQTT broker address or hostname observed on the
  router.
- `upstream_port`: vendor MQTT port; defaults to `1883`.
- `poll_interval`: local telemetry polling interval in seconds. `2.0` is
  recommended for the tested RWB1; `0` disables local polling.
- `verbose`: additional diagnostic logging without credentials or complete
  topics.

## Network

The app listens on TCP port `18830` of the Home Assistant host. OpenWrt must
redirect only traffic from the datalogger IP address to the vendor cloud MQTT
broker. If OpenWrt and Home Assistant are on different subnets, that flow also
requires SNAT/MASQUERADE to preserve the return path.

Start with temporary rules. Make them persistent only after confirming all of
the following:

- the datalogger remains online in the vendor app;
- telemetry appears in the app log;
- the MQTT integration creates the Home Assistant entities.

The request envelope required for local polling is learned from a legitimate
cloud request and stored in the app's private persistent storage. It is never
logged or committed. Local requests are serialized with cloud requests, and
their responses are not forwarded to the cloud. The private file may be
included in app backups, which must be stored securely.

This version never sends Modbus write functions. Local polling is hard-coded to
the allow-listed telemetry block starting at `0x1195`.

## Full documentation

- [Installation guide](https://github.com/jpedrotas/easun-mqtt-bridge/blob/main/docs/INSTALLATION.md)
- [Tested versions](https://github.com/jpedrotas/easun-mqtt-bridge/blob/main/docs/TESTED_VERSIONS.md)
- [Troubleshooting](https://github.com/jpedrotas/easun-mqtt-bridge/blob/main/docs/TROUBLESHOOTING.md)
