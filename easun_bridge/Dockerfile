# https://developers.home-assistant.io/docs/apps/configuration#app-dockerfile
ARG BUILD_FROM=ghcr.io/home-assistant/base:3.23
FROM ${BUILD_FROM}

ARG BUILD_VERSION
ARG BUILD_ARCH

RUN apk add --no-cache python3

WORKDIR /app
COPY easun_bridge.py /app/easun_bridge.py
COPY run.sh /run.sh

RUN chmod 0755 /run.sh /app/easun_bridge.py

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 -c "import socket; socket.create_connection(('127.0.0.1', 18830), 3).close()" || exit 1

CMD ["/run.sh"]

LABEL \
    io.hass.version="${BUILD_VERSION}" \
    io.hass.type="app" \
    io.hass.arch="${BUILD_ARCH}" \
    org.opencontainers.image.title="Home Assistant App: EASUN MQTT Bridge" \
    org.opencontainers.image.description="Local read-only telemetry bridge for EASUN RWB1 dataloggers" \
    org.opencontainers.image.licenses="MIT"
