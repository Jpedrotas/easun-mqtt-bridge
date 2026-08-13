#!/bin/sh
set -eu

DNAT_SECTION='easun_bridge_dnat'
SNAT_SECTION='easun_bridge_snat'
APPLY=0

usage() {
    cat <<'EOF'
Usage:
  easun-bridge-firewall.sh install [--apply]
  easun-bridge-firewall.sh remove [--apply]
  easun-bridge-firewall.sh status

install and remove are dry-run operations unless --apply is supplied.

Required environment variables for install:
  DATALOGGER_IP       IPv4 address of the RWB1 datalogger
  CLOUD_MQTT_IP       IPv4 address of the vendor MQTT broker
  HOME_ASSISTANT_IP   IPv4 address of the Home Assistant host

Optional environment variables:
  CLOUD_MQTT_PORT     Vendor MQTT TCP port (default: 1883)
  BRIDGE_PORT         EASUN bridge TCP port (default: 18830)
  SOURCE_ZONE         OpenWrt zone containing the datalogger (default: lan)
  DESTINATION_ZONE    OpenWrt zone used to reach Home Assistant (default: lan)
  ENABLE_SNAT         1 to enable source NAT, 0 to disable it (default: 1)
EOF
}

fail() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

valid_ipv4() {
    value="$1"
    case "$value" in
        *[!0-9.]* | *.*.*.*.* | .* | *.) return 1 ;;
    esac
    old_ifs="$IFS"
    IFS='.'
    set -- $value
    IFS="$old_ifs"
    [ "$#" -eq 4 ] || return 1
    for octet in "$@"; do
        [ -n "$octet" ] || return 1
        [ "$octet" -ge 0 ] 2>/dev/null || return 1
        [ "$octet" -le 255 ] 2>/dev/null || return 1
    done
}

valid_port() {
    [ "$1" -ge 1 ] 2>/dev/null && [ "$1" -le 65535 ] 2>/dev/null
}

zone_exists() {
    zone="$1"
    uci show firewall 2>/dev/null |
        grep -Eq "^firewall\.[^.]+\.name=['\"]?$zone['\"]?$"
}

show_command() {
    printf '+ '
    printf "'%s' " "$@"
    printf '\n'
}

run() {
    if [ "$APPLY" -eq 1 ]; then
        "$@"
    else
        show_command "$@"
    fi
}

delete_section() {
    section="$1"
    if [ "$APPLY" -eq 1 ]; then
        uci -q delete "$section" 2>/dev/null || true
    else
        show_command uci -q delete "$section"
    fi
}

validate_runtime() {
    command_exists uci || fail 'uci is not available'
    command_exists fw4 || fail 'firewall4 (fw4) is required; use OpenWrt 22.03 or newer'
    [ -r /etc/config/firewall ] || fail '/etc/config/firewall is not readable'
}

install_rules() {
    : "${DATALOGGER_IP:?Set DATALOGGER_IP}"
    : "${CLOUD_MQTT_IP:?Set CLOUD_MQTT_IP}"
    : "${HOME_ASSISTANT_IP:?Set HOME_ASSISTANT_IP}"

    CLOUD_MQTT_PORT="${CLOUD_MQTT_PORT:-1883}"
    BRIDGE_PORT="${BRIDGE_PORT:-18830}"
    SOURCE_ZONE="${SOURCE_ZONE:-lan}"
    DESTINATION_ZONE="${DESTINATION_ZONE:-lan}"
    ENABLE_SNAT="${ENABLE_SNAT:-1}"

    valid_ipv4 "$DATALOGGER_IP" || fail 'DATALOGGER_IP is not a valid IPv4 address'
    valid_ipv4 "$CLOUD_MQTT_IP" || fail 'CLOUD_MQTT_IP is not a valid IPv4 address'
    valid_ipv4 "$HOME_ASSISTANT_IP" || fail 'HOME_ASSISTANT_IP is not a valid IPv4 address'
    valid_port "$CLOUD_MQTT_PORT" || fail 'CLOUD_MQTT_PORT is invalid'
    valid_port "$BRIDGE_PORT" || fail 'BRIDGE_PORT is invalid'
    [ "$ENABLE_SNAT" = '0' ] || [ "$ENABLE_SNAT" = '1' ] || fail 'ENABLE_SNAT must be 0 or 1'
    zone_exists "$SOURCE_ZONE" || fail "SOURCE_ZONE '$SOURCE_ZONE' does not exist"
    zone_exists "$DESTINATION_ZONE" || fail "DESTINATION_ZONE '$DESTINATION_ZONE' does not exist"
    [ "$DATALOGGER_IP" != "$HOME_ASSISTANT_IP" ] || fail 'Datalogger and Home Assistant IP addresses must differ'

    backup="/root/firewall.before-easun-$(date +%Y%m%d-%H%M%S)"
    printf 'Installing exact match: %s -> %s:%s redirected to %s:%s\n' \
        "$DATALOGGER_IP" "$CLOUD_MQTT_IP" "$CLOUD_MQTT_PORT" "$HOME_ASSISTANT_IP" "$BRIDGE_PORT"
    printf 'Zones: source=%s destination=%s; source NAT=%s\n' \
        "$SOURCE_ZONE" "$DESTINATION_ZONE" "$ENABLE_SNAT"

    run cp /etc/config/firewall "$backup"
    delete_section "firewall.$DNAT_SECTION"
    run uci set "firewall.$DNAT_SECTION=redirect"
    run uci set "firewall.$DNAT_SECTION.name=EASUN bridge DNAT"
    run uci set "firewall.$DNAT_SECTION.family=ipv4"
    run uci set "firewall.$DNAT_SECTION.proto=tcp"
    run uci set "firewall.$DNAT_SECTION.src=$SOURCE_ZONE"
    run uci set "firewall.$DNAT_SECTION.src_ip=$DATALOGGER_IP"
    run uci set "firewall.$DNAT_SECTION.src_dip=$CLOUD_MQTT_IP"
    run uci set "firewall.$DNAT_SECTION.src_dport=$CLOUD_MQTT_PORT"
    run uci set "firewall.$DNAT_SECTION.dest=$DESTINATION_ZONE"
    run uci set "firewall.$DNAT_SECTION.dest_ip=$HOME_ASSISTANT_IP"
    run uci set "firewall.$DNAT_SECTION.dest_port=$BRIDGE_PORT"
    run uci set "firewall.$DNAT_SECTION.target=DNAT"
    run uci set "firewall.$DNAT_SECTION.reflection=0"
    run uci set "firewall.$DNAT_SECTION.enabled=1"

    delete_section "firewall.$SNAT_SECTION"
    if [ "$ENABLE_SNAT" = '1' ]; then
        run uci set "firewall.$SNAT_SECTION=nat"
        run uci set "firewall.$SNAT_SECTION.name=EASUN bridge SNAT"
        run uci set "firewall.$SNAT_SECTION.family=ipv4"
        run uci set "firewall.$SNAT_SECTION.proto=tcp"
        run uci set "firewall.$SNAT_SECTION.src=$SOURCE_ZONE"
        run uci set "firewall.$SNAT_SECTION.src_ip=$DATALOGGER_IP"
        run uci set "firewall.$SNAT_SECTION.dest_ip=$HOME_ASSISTANT_IP"
        run uci set "firewall.$SNAT_SECTION.dest_port=$BRIDGE_PORT"
        run uci set "firewall.$SNAT_SECTION.target=MASQUERADE"
        run uci set "firewall.$SNAT_SECTION.enabled=1"
    fi

    run uci commit firewall
    if [ "$APPLY" -eq 1 ]; then
        if ! fw4 check; then
            cp "$backup" /etc/config/firewall
            fw4 check >/dev/null 2>&1 || true
            fail "firewall validation failed; restored $backup"
        fi
        /etc/init.d/firewall reload
        printf 'Installed successfully. Backup: %s\n' "$backup"
    else
        printf '\nDry run only. Re-run with --apply after checking every value.\n'
    fi
}

remove_rules() {
    backup="/root/firewall.before-easun-remove-$(date +%Y%m%d-%H%M%S)"
    run cp /etc/config/firewall "$backup"
    delete_section "firewall.$DNAT_SECTION"
    delete_section "firewall.$SNAT_SECTION"
    run uci commit firewall
    if [ "$APPLY" -eq 1 ]; then
        if ! fw4 check; then
            cp "$backup" /etc/config/firewall
            fw4 check >/dev/null 2>&1 || true
            fail "firewall validation failed; restored $backup"
        fi
        /etc/init.d/firewall reload
        printf 'EASUN bridge firewall sections removed. Backup: %s\n' "$backup"
    else
        printf '\nDry run only. Re-run with --apply to remove the rules.\n'
    fi
}

status_rules() {
    printf '%s\n' '--- DNAT section ---'
    uci show "firewall.$DNAT_SECTION" 2>/dev/null || printf 'not installed\n'
    printf '%s\n' '--- SNAT section ---'
    uci show "firewall.$SNAT_SECTION" 2>/dev/null || printf 'not installed\n'
    printf '%s\n' '--- firewall validation ---'
    fw4 check
}

[ "$#" -ge 1 ] || { usage; exit 1; }
ACTION="$1"
shift
if [ "${1:-}" = '--apply' ]; then
    APPLY=1
    shift
fi
[ "$#" -eq 0 ] || { usage; exit 1; }

validate_runtime
case "$ACTION" in
    install) install_rules ;;
    remove) remove_rules ;;
    status) [ "$APPLY" -eq 0 ] || fail '--apply is not valid with status'; status_rules ;;
    *) usage; exit 1 ;;
esac
