# Compatibility matrix

Compatibility depends on the complete chain: inverter, datalogger, datalogger
firmware, router hardware, OpenWrt release, firewall generation, Home Assistant
hardware, and Home Assistant software. A matching product name alone is not
enough.

See [`SOURCES.md`](SOURCES.md) for the source behind each class of claim and the
policy used to distinguish confirmed observations from compatibility inferences.

## Confirmed test system

| Layer | Hardware/software | Version or revision | Evidence/status |
|---|---|---|---|
| Inverter | EASUN iSolar SMH III | 4.2 kW; exact inverter firmware not exposed | Hardware confirmed; firmware pending |
| Datalogger | Solar Plug-RWB1 | Type `04`; commercial reference `ECOMAX-730-70081-00` | Confirmed from device labels |
| Datalogger firmware | RWB1 embedded firmware | Not exposed by the vendor UI used during testing | Unknown; do not assume compatibility across revisions |
| Datalogger protocol | MQTT 3.1.1 over TCP | JSON with Base64-encoded Modbus RTU frames | Confirmed from captures |
| Original router | TP-Link Archer C20 | Hardware revision v5 | Confirmed from the archived OpenWrt configuration/device identifiers |
| Original router firmware | OpenWrt | 19.07 generation; exact point release not preserved | Generation inferred from the installed feed keys and legacy configuration |
| Original firewall | firewall3 | `iptables` and `/etc/firewall.user` | Confirmed from archived configuration |
| Home Assistant host | Raspberry Pi 4 | 2 GB RAM | Confirmed test host |
| Home Assistant host architecture | Raspberry Pi 4 64-bit (`rpi4-64`) | `aarch64`; kernel `6.18.34-haos-raspi` | Confirmed from host information |
| Home Assistant Core | Home Assistant | 2026.8.1 | Confirmed during validation |
| Home Assistant OS | Home Assistant OS | 18.2 | Confirmed during validation |
| Supervisor | Home Assistant Supervisor | 2026.07.5 | Confirmed during validation |
| Local MQTT | Official Mosquitto Broker app | 7.1.0 | Confirmed and running during validation |
| Bridge | EASUN MQTT Bridge | 0.3.2 | Passive proxy and two-second polling confirmed |
| Vendor client | Sun House app / Siseli web platform | Exact app and web build versions not recorded | Used to trigger and compare cloud requests |

## Network infrastructure present during testing

The test site had a more complex network than the minimal diagrams. The
following equipment was present, although not every device was necessarily in
the packet path during every capture:

| Equipment | Role during testing | Version status |
|---|---|---|
| Vodafone ISP gateway | Main Internet gateway and DHCP network | Exact model and firmware not recorded |
| TP-Link Deco system | Multi-node Wi-Fi mesh with wired backhaul on at least the main node | Exact models, hardware revisions, and firmware not recorded |
| Ethernet switch | Connected the main Deco path to the Vodafone gateway | Manufacturer/model not recorded |
| TP-Link Archer C6 | Additional access point/router connected by Ethernet | Hardware revision and official firmware not recorded |
| Second TP-Link Archer C20 | Official-firmware Wi-Fi repeater | Hardware revision and official firmware not recorded |
| TP-Link Archer C20 v5 | OpenWrt interception router | OpenWrt 19.07 generation; exact point release not preserved |

An official TP-Link Archer C20 v5 firmware package labelled version
`0.9.1 4.17`, build `260317` (`2026-03-17`), was downloaded during router
maintenance. It is **not** listed as an installed/tested firmware because the
active router firmware was not queried after that operation. A downloaded image
is not proof of installation.

This topology matters. A wireless client can associate through a Deco, C6, or
repeater and bypass the OpenWrt interception router. For reliable operation, the
RWB1 must use a dedicated SSID or otherwise have a deterministic path through
OpenWrt.

No serial number, device ID, MAC address, private address, credential, or MQTT
topic is required in a public compatibility report.

## Current replacement router

The current tutorial has been rewritten for a newer replacement router using
OpenWrt 22.03 or newer with firewall4/nftables. Its exact values must be entered
after installation and validation:

| Item | Value |
|---|---|
| Router manufacturer/model | Pending |
| Hardware revision | Pending |
| CPU target/architecture | Pending |
| Bootloader constraints | Pending/not required by the bridge |
| OpenWrt exact release | Pending |
| Kernel version | Pending |
| firewall4 version | Pending |
| nftables version | Pending |
| Wireless driver/firmware | Pending |
| Connection role | Pending: routed client, repeater, access point, or wired router |
| Passive proxy validation | Pending |
| Two-second polling validation | Pending |

The supplied firewall script requires `fw4` and therefore intentionally does
not run on the original OpenWrt 19.07/firewall3 environment.

## Compatibility levels

- **Confirmed**: the exact hardware/revision and software combination completed
  passive proxying and local polling.
- **Likely**: the same protocol family is documented, but the exact combination
  has not been tested.
- **Unknown**: a firmware or hardware revision was not visible or preserved.
- **Unsupported**: the protocol differs, MQTT is encrypted, the router cannot
  intercept the traffic path, or the platform architecture is not built.

## Known boundaries

- The Home Assistant app currently declares `aarch64` and `amd64`. The original
  Raspberry Pi 4 installation uses `aarch64`.
- The bridge expects MQTT 3.1.1 over unencrypted TCP and cannot inspect MQTT over
  TLS without a different, explicitly designed architecture.
- Only Modbus slave `5` and the confirmed 21-word telemetry response have been
  validated.
- Local polling is allow-listed to the block starting at `0x1195`.
- Other SMH III power ratings may use the Sumry family but remain unconfirmed.
- Different RWB1 firmware may change the private request envelope or reject
  locally generated requests.
- Wi-Fi repeaters, mesh systems, and multiple routers can cause the datalogger
  to bypass the intended OpenWrt path.

## Before reporting compatibility

Collect the non-sensitive inventory described in
[`docs/HARDWARE_SOFTWARE_INVENTORY.md`](docs/HARDWARE_SOFTWARE_INVENTORY.md).
Remove network addresses and unique identifiers before sharing it.
