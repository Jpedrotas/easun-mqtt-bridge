# EASUN MQTT Bridge

Proxy MQTT transparente e experimental para o datalogger RWB1 usado com alguns
inversores EASUN iSolar SMH III. Encaminha a ligação original para a cloud,
valida e descodifica os frames Modbus RTU e pode publicar a telemetria confirmada
num broker MQTT local com Home Assistant MQTT Discovery.

O funcionamento da aplicação do fabricante é preservado. O bridge não guarda
nem mostra as credenciais MQTT do datalogger, não envia comandos ao inversor e
não permite escritas de parâmetros.

> Estado: o proxy transparente foi validado num único SMH III 4,2 kW/RWB1,
> mantendo a telemetria e as consultas da aplicação do fabricante. O pacote do
> Home Assistant ainda está em validação e não deve ser usado como única fonte
> de monitorização ou controlo.

## Arquitetura

```text
datalogger RWB1 -> OpenWrt -> EASUN MQTT Bridge -> broker da cloud
                                    |
                                    +-> Mosquitto local -> Home Assistant
```

O redirecionamento deve limitar-se ao IP do datalogger e ao destino/porto MQTT
observado. As regras de exemplo para OpenWrt só serão adicionadas depois da
validação do teste real.

## Teste local

```powershell
python .\test_easun_bridge.py
python .\easun_bridge\easun_bridge.py --listen-port 18830 --upstream-host <broker-da-cloud>
```

## Home Assistant

O diretório [`easun_bridge`](easun_bridge) contém uma aplicação instalável no
Home Assistant OS. Usa automaticamente as credenciais de serviço geradas pelo
Mosquitto oficial; estas não ficam na configuração nem nos logs.

Para execução fora do Home Assistant, as credenciais do broker local, quando
necessárias, são fornecidas apenas por variáveis de ambiente:

```text
EASUN_LOCAL_MQTT_USERNAME
EASUN_LOCAL_MQTT_PASSWORD
```

Depois inicia-se o proxy com `--local-mqtt-host <endereço-do-broker>`. Nunca
coloque credenciais na linha de comandos, no repositório ou nos logs.

Os sensores publicados são apenas os campos confirmados e documentados em
[`REGISTER_MAP.md`](REGISTER_MAP.md). Os campos ainda ambíguos estão claramente
marcados com confiança média.

O hardware efetivamente testado está identificado, sem números de série ou
outros dados privados, em [`COMPATIBILITY.md`](COMPATIBILITY.md).

## Privacidade e segurança

- Não submeter PCAPs, credenciais, endereços MAC, identificadores de dispositivo
  ou tópicos MQTT completos.
- Usar primeiro o modo passivo; este projeto não implementa escrita Modbus.
- Manter uma forma local de remover o redirecionamento se a cloud deixar de
  funcionar.

## Licença

MIT. Os projetos externos indicados no mapa de registos foram usados apenas
como referência de interoperabilidade; não foi copiado código desses projetos.
