#!/usr/bin/with-contenv bashio
set -euo pipefail

UPSTREAM_HOST="$(bashio::config 'upstream_host')"
UPSTREAM_PORT="$(bashio::config 'upstream_port')"
POLL_INTERVAL="$(bashio::config 'poll_interval')"
if [[ ! "${POLL_INTERVAL}" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
    POLL_INTERVAL="2.0"
fi

if ! bashio::var.has_value "${UPSTREAM_HOST}"; then
    bashio::exit.nok "Configure upstream_host with the vendor MQTT broker address observed on the router"
fi

if ! bashio::var.has_value "$(bashio::services 'mqtt')"; then
    bashio::exit.nok "The Home Assistant MQTT service is unavailable"
fi

export EASUN_LOCAL_MQTT_USERNAME="$(bashio::services 'mqtt' 'username')"
export EASUN_LOCAL_MQTT_PASSWORD="$(bashio::services 'mqtt' 'password')"
MQTT_HOST="$(bashio::services 'mqtt' 'host')"
MQTT_PORT="$(bashio::services 'mqtt' 'port')"

ARGS=(
    --listen-host 0.0.0.0
    --listen-port 18830
    --upstream-host "${UPSTREAM_HOST}"
    --upstream-port "${UPSTREAM_PORT}"
    --local-mqtt-host "${MQTT_HOST}"
    --local-mqtt-port "${MQTT_PORT}"
    --template-cache /data/read-template.json
    --poll-interval "${POLL_INTERVAL}"
)

if bashio::config.true 'verbose'; then
    ARGS+=(--verbose)
fi

bashio::log.info "Starting EASUN MQTT bridge"
exec python3 /app/easun_bridge.py "${ARGS[@]}"
