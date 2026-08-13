# Hardware and software inventory

Complete this inventory before installation and again after any firmware or
network change. Versions that are unavailable should be marked **unknown**, not
guessed.

## Inverter and datalogger

| Item | Where to find it | Record |
|---|---|---|
| Inverter manufacturer/model/rating | Rating plate and manual | Model only; redact serial number |
| Inverter firmware | LCD information menu or vendor app, if exposed | Main/control/display versions separately |
| Datalogger model and type | Device or packaging label | Model and type; redact ID and QR code |
| Datalogger hardware revision | Label or vendor information page | Revision only |
| Datalogger firmware | Vendor app/device information page | Exact version if exposed |
| Vendor app | Android/iOS app information | App name and version |
| Cloud endpoint protocol | Short private capture | Protocol and port only; never publish credentials/topics |

If firmware versions are not visible, write `unknown (not exposed by device)`.
Do not use firmware download filenames as proof that the firmware is installed.

## OpenWrt router

Run locally on the router:

```sh
ubus call system board
cat /etc/openwrt_release
uname -a
fw4 -V 2>/dev/null || fw3 -V 2>/dev/null
nft --version 2>/dev/null || iptables --version
opkg list-installed | grep -E '^(firewall|firewall4|luci|wpad|hostapd) '
```

Record:

- router model and hardware revision;
- OpenWrt exact release and target;
- kernel, firewall, and nftables/iptables versions;
- wireless package/driver and firmware when the router connects upstream by
  Wi-Fi;
- the router role: routed gateway, wireless client, repeater, access point, or
  bridge;
- firewall zone names used by the datalogger and Home Assistant paths.

Do not publish the full `ubus`, wireless, or firewall output without redacting
hostnames, SSIDs, keys, MAC addresses, and IP addresses.

## Home Assistant

In **Settings → System → Repairs → System information**, record:

- Home Assistant Core version;
- Home Assistant OS version;
- Supervisor version;
- installation type and CPU architecture;
- host model and installed RAM;
- Mosquitto Broker app version;
- MQTT integration status;
- EASUN MQTT Bridge version.

For the confirmed Raspberry Pi 4 test host, the baseline was Home Assistant Core
2026.8.1, OS 18.2, Supervisor 2026.07.5, kernel
`6.18.34-haos-raspi`, and Mosquitto Broker app 7.1.0.

Also record whether port `18830` is enabled and whether Home Assistant is on the
same subnet as OpenWrt. Never share backup files or diagnostic downloads without
reviewing them for secrets.

## Network hardware and topology

List every device that can affect the packet path:

- ISP router;
- Ethernet switches and VLANs;
- mesh nodes;
- Wi-Fi repeaters;
- access points;
- the OpenWrt router;
- Home Assistant host;
- datalogger.

For each router/repeater/AP, record model, hardware revision, installed firmware,
operating mode, and whether the connection is wired or wireless. A topology can
work intermittently if a datalogger roams to an access point whose path bypasses
OpenWrt.

## Revalidation triggers

Repeat passive and active validation after any of the following:

- inverter or datalogger firmware update;
- OpenWrt upgrade or router replacement;
- firewall3-to-firewall4 migration;
- Home Assistant or Mosquitto major update;
- change from wired backhaul to Wi-Fi/repeater mode;
- DHCP, VLAN, subnet, mesh, DNS, or vendor endpoint change.

Keep the inventory in a private file. Publish only the minimum non-sensitive
version matrix needed to establish compatibility.
