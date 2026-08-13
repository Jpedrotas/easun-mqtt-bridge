# Installation guide

This guide installs EASUN MQTT Bridge as a Home Assistant app and redirects only
the RWB1 datalogger MQTT connection through it. Read the complete guide before
changing the router firewall.

## What you need

- Home Assistant OS on an `aarch64` or `amd64` system.
- The official Mosquitto Broker app and the MQTT integration.
- An OpenWrt router through which the RWB1 traffic passes.
- Administrator access to Home Assistant and SSH or LuCI access to OpenWrt.
- A fixed DHCP lease for the datalogger and preferably for Home Assistant.
- The IPv4 address and TCP port of the vendor MQTT broker used by the dongle.

OpenWrt 22.03 or newer is recommended. These versions use firewall4/nftables but
retain the UCI firewall configuration used in this guide.

The original development router was an Archer C20 v5 running the OpenWrt 19.07
generation with firewall3/iptables. The current guide intentionally targets a
newer router and firewall4 to make installation persistent and easier to undo.
See [`TESTED_VERSIONS.md`](TESTED_VERSIONS.md) before comparing these steps with
older screenshots or development notes.

Official references used by this guide:

- [Home Assistant app repository installation](https://developers.home-assistant.io/docs/apps/repository/)
- [OpenWrt firewall configuration](https://openwrt.org/docs/guide-user/firewall/firewall_configuration)

## Network flow

### Scenario A: datalogger and Home Assistant on the same network

```text
Internet / vendor MQTT broker
             |
         OpenWrt router
          /          \
 RWB1 datalogger   Home Assistant
```

The router rewrites the selected datalogger connection to Home Assistant port
`18830`. Source NAT is recommended so replies always return through OpenWrt.

### Scenario B: isolated datalogger network

```text
Internet / vendor MQTT broker
             |
      upstream home network -------- Home Assistant
             |
        OpenWrt WAN
        OpenWrt LAN
             |
       RWB1 datalogger
```

Use the OpenWrt zone containing the datalogger as `SOURCE_ZONE` and the zone
used to reach Home Assistant as `DESTINATION_ZONE`. Source NAT is normally
required because Home Assistant otherwise returns traffic through its default
gateway instead of OpenWrt.

## 1. Reserve addresses

Create fixed DHCP leases for the RWB1 and Home Assistant. Do not continue while
either address can change. Record these values without publishing them:

```text
DATALOGGER_IP=
HOME_ASSISTANT_IP=
CLOUD_MQTT_IP=
CLOUD_MQTT_PORT=1883
SOURCE_ZONE=lan
DESTINATION_ZONE=lan or wan
```

The zone is a firewall zone name, not necessarily an interface name. Check it
with:

```sh
uci show firewall | grep '=zone'
ubus call network.interface dump
```

## 2. Identify the vendor MQTT destination

Before installing any redirect, start a temporary capture on OpenWrt:

```sh
tcpdump -ni any host <DATALOGGER_IP> and tcp
```

Power-cycle the dongle and look for an outbound connection, commonly on TCP
port `1883`. Record the remote IPv4 address and port. Stop the capture with
`Ctrl+C` and do not publish its output: MQTT may be unencrypted and contain
credentials or unique identifiers.

If `tcpdump` is unavailable:

```sh
opkg update
opkg install tcpdump-mini
```

Some vendor hostnames resolve to several or changing IP addresses. A redirect
that matches one `CLOUD_MQTT_IP` stops matching if the vendor changes address.
Confirm the destination again whenever the bridge unexpectedly stops receiving
connections.

## 3. Install the Home Assistant app

[![Open the Home Assistant app store and add this repository](https://my.home-assistant.io/badges/supervisor_store.svg)](https://my.home-assistant.io/redirect/supervisor_store/?repository_url=https%3A%2F%2Fgithub.com%2Fjpedrotas%2Feasun-mqtt-bridge)

Alternatively:

1. Open **Settings → Apps → App store**.
2. Open the repository menu.
3. Add `https://github.com/jpedrotas/easun-mqtt-bridge`.
4. Install **EASUN MQTT Bridge**.
5. Do not start it yet.

Configure:

```yaml
upstream_host: <vendor MQTT hostname or IPv4 address>
upstream_port: 1883
poll_interval: 0
verbose: false
```

Start with `poll_interval: 0`. This validates transparent proxying before local
polling is enabled. Start the app and confirm that its log says it is listening
on port `18830` and connected to the local MQTT broker.

## 4. Test reachability before redirecting

From OpenWrt:

```sh
nc -zvw3 <HOME_ASSISTANT_IP> 18830
```

If the BusyBox `nc` build has no `-z`, use:

```sh
nc -vw3 <HOME_ASSISTANT_IP> 18830 </dev/null
```

Do not configure DNAT until this succeeds. Check the Home Assistant app is
running, port `18830` is enabled, and routing between the two networks works.

## 5. Install the OpenWrt rules safely

Copy [`openwrt/easun-bridge-firewall.sh`](../openwrt/easun-bridge-firewall.sh) to
`/root/easun-bridge-firewall.sh` on OpenWrt, then:

```sh
chmod 700 /root/easun-bridge-firewall.sh
```

Export installation-specific values:

```sh
export DATALOGGER_IP='<datalogger IPv4>'
export CLOUD_MQTT_IP='<vendor broker IPv4>'
export CLOUD_MQTT_PORT='1883'
export HOME_ASSISTANT_IP='<Home Assistant IPv4>'
export SOURCE_ZONE='lan'
export DESTINATION_ZONE='<lan-or-wan>'
```

Preview without changing anything:

```sh
/root/easun-bridge-firewall.sh install
```

Read every command. Apply only when all addresses and zones are correct:

```sh
/root/easun-bridge-firewall.sh install --apply
```

The script creates a timestamped backup of `/etc/config/firewall`, writes two
named UCI sections, validates them with `fw4 check`, and reloads the firewall.
It defaults to source NAT because that is reliable in both network scenarios.

Inspect the result:

```sh
/root/easun-bridge-firewall.sh status
fw4 print | grep -i easun
```

### LuCI alternative

LuCI writes the same UCI configuration, but field names vary by OpenWrt release
and theme. SSH with the supplied script is the reference method. On recent LuCI
versions, the equivalent DNAT rule is usually under **Network → Firewall → Port
Forwards**:

| LuCI field | Value |
|---|---|
| Name | `EASUN bridge DNAT` |
| Protocol | TCP |
| Source zone | Zone containing the datalogger |
| External/source IP | Vendor MQTT broker IPv4 |
| External port | Vendor MQTT port, normally `1883` |
| Source IP restriction | Datalogger IPv4 |
| Destination zone | Zone used to reach Home Assistant |
| Internal IP | Home Assistant IPv4 |
| Internal port | `18830` |
| NAT reflection | Disabled |

Recent LuCI builds may also expose **NAT Rules**. Add a narrowly scoped
masquerade rule for TCP traffic from the datalogger to Home Assistant port
`18830`. If the page does not expose source and destination restrictions, do not
create a broad masquerade rule; use the script instead.

Before **Save & Apply**, back up `/etc/config/firewall`. Afterwards, run over
SSH:

```sh
fw4 check
uci show firewall | grep -i easun
```

Do not use both LuCI rules and the script at the same time, or the redirect may
be duplicated.

## 6. Validate passive operation

Power-cycle the dongle or wait for it to reconnect. Confirm all three results:

1. The vendor app reports the dongle online.
2. The bridge log reports a datalogger connection and valid Modbus frames.
3. Home Assistant creates an **EASUN MQTT Bridge** device through MQTT
   Discovery.

Leave `poll_interval: 0` until the vendor app and passive telemetry have worked
for several minutes.

## 7. Enable local polling

Set:

```yaml
poll_interval: 2.0
```

Restart the app. The bridge first learns a legitimate request envelope from the
cloud and stores it privately in `/data`. Local values should then refresh about
every two seconds. The first active update may be delayed until the vendor cloud
sends a suitable request.

Do not use an interval below two seconds unless you are prepared to diagnose
dongle instability. `0` disables local polling immediately after an app restart.

## 8. Roll back

If the vendor app goes offline or any network problem appears, remove only the
bridge rules:

```sh
/root/easun-bridge-firewall.sh remove --apply
```

Then power-cycle the datalogger. To restore the complete firewall file from the
backup reported during installation:

```sh
cp /root/firewall.before-easun-<timestamp> /etc/config/firewall
fw4 check && /etc/init.d/firewall reload
```

Never delete unrelated firewall rules. If router access is lost, use a wired
connection or OpenWrt failsafe mode and restore the saved file.

## Next steps

- Read [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md).
- Protect Home Assistant backups because they can include the private request
  envelope.
- Keep the datalogger redirect restricted to its source IP, vendor destination,
  and MQTT port.
