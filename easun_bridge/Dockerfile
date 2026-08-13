# https://developers.home-assistant.io/docs/apps/configuration#app-dockerfile
ARG BUILD_FROM=ghcr.io/home-assistant/base:3.23
FROM ${BUILD_FROM}

RUN apk add --no-cache python3

WORKDIR /app
COPY easun_bridge.py /app/easun_bridge.py
COPY run.sh /run.sh

RUN chmod 0755 /run.sh /app/easun_bridge.py

CMD ["/run.sh"]

LABEL \
    org.opencontainers.image.title="Home Assistant App: EASUN MQTT Bridge" \
    org.opencontainers.image.description="Passive transparent MQTT bridge for EASUN RWB1 dataloggers" \
    org.opencontainers.image.licenses="MIT"
