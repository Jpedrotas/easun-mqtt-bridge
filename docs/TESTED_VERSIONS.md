# Tested versions and version differences

The project was developed in stages, and the router used for the original
traffic capture was not the same generation as the router targeted by the
current installation guide.

## Original development environment

The protocol investigation and first working redirect were performed with:

| Component | Version or platform |
|---|---|
| Inverter | EASUN iSolar SMH III 4.2 kW |
| Datalogger | Solar Plug-RWB1, type 04 |
| Original OpenWrt router | TP-Link Archer C20 v5 |
| Original OpenWrt generation | OpenWrt 19.07 family |
| Original firewall engine | firewall3 with `iptables` and `/etc/firewall.user` |
| Home Assistant Core | 2026.8.1 |
| Home Assistant OS | 18.2 |
| Home Assistant Supervisor | 2026.07.5 |
| Home Assistant hardware | Raspberry Pi 4 with 2 GB RAM |
| Home Assistant architecture/kernel | `rpi4-64` / `aarch64`; `6.18.34-haos-raspi` |
| Mosquitto Broker app | 7.1.0 |
| Bridge release | 0.3.2 |

The wider test network also included a Vodafone ISP gateway, a TP-Link Deco
mesh, an Ethernet switch, a TP-Link Archer C6, and a second Archer C20 running
official firmware as a Wi-Fi repeater. Their exact hardware and firmware
versions were not recorded and are therefore marked as unknown in the
[compatibility matrix](../COMPATIBILITY.md). They are documented because mesh
roaming or repeater paths can bypass the interception router.

The archived original router configuration uses the legacy firewall3 format and
an `iptables`-based `/etc/firewall.user`. This is why early development notes or
screenshots may differ from the current tutorial.

An official Archer C20 v5 firmware package version `0.9.1 4.17`, build
`260317`, was available during later router maintenance. Its installed state was
not confirmed, so it is recorded as a candidate package rather than a tested
firmware version.

## Current recommended installation environment

To make installation safer and easier on a new router, the published tutorial
and helper script target:

| Component | Recommended version |
|---|---|
| OpenWrt | 22.03 or newer |
| Firewall | firewall4 (`fw4`) with nftables |
| Configuration method | Persistent UCI sections in `/etc/config/firewall` |
| Home Assistant | A currently supported version with Apps and MQTT Discovery |
| Mosquitto | Official Home Assistant Mosquitto Broker app |

The exact modern OpenWrt release must still be recorded after the replacement
router is installed and validated. OpenWrt 22.03 is the minimum for the supplied
script, not a claim that every later release and every hardware target has
already been tested.

## Why the instructions differ

- OpenWrt 19.07 uses firewall3/`iptables`; modern OpenWrt uses
  firewall4/`nftables`.
- Raw `iptables` commands from the original test are not the recommended public
  installation method and may disappear after a firewall restart on modern
  OpenWrt.
- The current script creates named UCI sections, validates them with `fw4 check`,
  and removes only its own rules.
- LuCI labels and menu locations can vary between OpenWrt releases and themes.
- Home Assistant renamed add-ons to apps; older screenshots may still show
  **Add-ons** instead of **Apps**.

## Legacy OpenWrt 19.07

The bridge can work with OpenWrt 19.07 because that was the original test
environment, but the supplied installer intentionally refuses to run without
`fw4`. Legacy installations require equivalent firewall3 UCI rules and careful
manual validation. Do not paste raw rules from an old installation without
changing all addresses, ports, interfaces, and zones.

For a new installation, upgrading to a supported OpenWrt release on compatible
hardware or using a newer OpenWrt router is strongly preferred. Never install an
image intended for a different router model or hardware revision.

## Reporting another working version

When reporting compatibility, include only non-sensitive details:

- router model and hardware revision;
- OpenWrt release and `fw4 -V` output;
- Home Assistant Core, OS, and Supervisor versions;
- inverter and datalogger model/type;
- whether passive mode and two-second polling both worked.

Do not include public IP addresses, private topology details, MAC addresses,
serial numbers, MQTT topics, credentials, or packet captures.
