# EASUN MQTT Bridge

Esta aplicação executa um proxy MQTT transparente e passivo para o datalogger
EASUN Solar Plug-RWB1. A ligação original continua a ser encaminhada para a
cloud do fabricante e a telemetria confirmada é publicada no Mosquitto local
através de MQTT Discovery.

## Antes de iniciar

1. Instale e inicie a aplicação oficial Mosquitto Broker.
2. Confirme que a integração MQTT do Home Assistant está ativa.
3. Determine o endereço do broker MQTT usado pelo dongle através de uma captura
   no router. Não publique a captura nem as credenciais encontradas.

## Opções

- `upstream_host`: endereço ou nome do broker MQTT da cloud observado no router.
- `upstream_port`: porto MQTT da cloud; por defeito `1883`.
- `verbose`: registo adicional para diagnóstico, sem credenciais nem tópicos
  completos.

## Rede

A aplicação escuta no porto TCP `18830` do Home Assistant. O OpenWrt deve
redirecionar exclusivamente o tráfego do IP do datalogger destinado ao broker
da cloud. Se o OpenWrt e o Home Assistant estiverem em sub-redes diferentes,
também é necessário aplicar SNAT/MASQUERADE nesse fluxo para garantir o caminho
de resposta.

Comece sempre com regras temporárias. Só as torne persistentes depois de
confirmar simultaneamente:

- o dongle online na aplicação do fabricante;
- telemetria no log da aplicação;
- entidades criadas pela integração MQTT no Home Assistant.

Esta versão não injeta pedidos e não escreve registos do inversor.
