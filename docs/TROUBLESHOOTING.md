# Troubleshooting

Work through this table from top to bottom. Change only one thing at a time.

| Symptom | Likely cause | Checks and solution |
|---|---|---|
| App will not start | Missing Mosquitto service or empty `upstream_host` | Start the official Mosquitto Broker app, verify the MQTT integration, and set the upstream host. |
| OpenWrt cannot reach port `18830` | App stopped, wrong Home Assistant IP, disabled port, or missing route | Check the app log, fixed lease, app network setting, `ip route`, and `nc -vw3 <HA_IP> 18830`. |
| No connection appears in bridge log | Wrong datalogger IP, cloud IP/port changed, traffic bypasses OpenWrt, or wrong source zone | Run a short `tcpdump` before the redirect, confirm the path and destination, then inspect `uci show firewall.easun_bridge_dnat`. |
| Vendor app goes offline immediately | Wrong `upstream_host`/port, bridge cannot reach cloud, or DNAT catches unrelated traffic | Remove the rules, confirm direct cloud operation, compare the captured destination with the app configuration, and reinstall only the exact match. |
| Bridge sees a connection but it closes repeatedly | Return path bypasses OpenWrt or cloud connection fails | Keep source NAT enabled, confirm `DESTINATION_ZONE`, test DNS and TCP access to the upstream broker from Home Assistant. |
| Passive values work but two-second polling does not start | No suitable cloud request has been observed yet | Open the device page in the vendor app, wait for a cloud refresh, and look for `Updated private local request template cache`. |
| Values remain on the cloud interval | `poll_interval` is `0`, old app version is running, or no private envelope exists | Set `2.0`, rebuild/reinstall version `0.3.1` or newer, restart, and trigger one legitimate cloud refresh. |
| Dongle becomes unstable after polling starts | Interval too aggressive or firmware incompatible | Set `poll_interval: 0`, restart the app, power-cycle the dongle, then retry at `5.0` seconds. |
| Entities do not appear in Home Assistant | MQTT Discovery unavailable or local broker authentication failed | Verify the MQTT integration, inspect Mosquitto and bridge logs, and listen to `homeassistant/sensor/easun_bridge/#` from a trusted MQTT client. |
| Entities are `unavailable` after restart | Dongle has not reconnected or bridge availability was not republished | Confirm the app and dongle are online, then restart only the bridge. |
| Vendor destination changed | DNS rotation or vendor infrastructure change | Capture a fresh connection, update `CLOUD_MQTT_IP`, reinstall the firewall rules, and update `upstream_host` only if the hostname/endpoint changed. |
| Internet through OpenWrt fails | Incorrect broad NAT/firewall rule or an unrelated network issue | Remove the bridge rules first. They should match one source IP, one destination IP, one TCP port only. Inspect the firewall diff against the backup. |
| LuCI/SSH access disappears after reload | Wrong firewall zone or unrelated firewall damage | Use a wired LAN connection or OpenWrt failsafe mode, restore `/root/firewall.before-easun-*`, and reload firewall. |
| Duplicate or stale MQTT entities | Previous discovery records retained | Keep the same `unique_id`; remove only obsolete retained discovery topics after taking an MQTT broker backup. Do not delete the complete MQTT database. |

## Useful commands

OpenWrt:

```sh
/root/easun-bridge-firewall.sh status
uci show firewall.easun_bridge_dnat
uci show firewall.easun_bridge_snat
fw4 check
fw4 print | grep -i easun
logread -e firewall
ip route get <HOME_ASSISTANT_IP>
tcpdump -ni any host <DATALOGGER_IP> and tcp
```

Home Assistant app log messages:

- `Read-only telemetry proxy listening`: the TCP listener is ready.
- `Datalogger connection accepted`: DNAT and routing reached the bridge.
- `Connected to local MQTT broker`: MQTT Discovery and state publication can
  operate.
- `Updated private local request template cache`: active polling can start.
- `Local telemetry polling healthy`: local responses are being decoded.

## Safe diagnostic order

1. Set `poll_interval: 0` and restart the app.
2. Remove the OpenWrt rules and confirm the vendor app works directly.
3. Confirm the exact datalogger, cloud, and Home Assistant addresses.
4. Confirm OpenWrt can reach Home Assistant port `18830`.
5. Reinstall the rules and validate passive operation.
6. Enable `poll_interval: 2.0` only after passive operation is stable.

Do not post complete packet captures or verbose logs publicly. Redact all
credentials, MQTT topics, serial numbers, device IDs, MAC addresses, and private
network details before asking for help.
