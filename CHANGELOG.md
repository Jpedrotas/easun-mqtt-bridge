# Changelog

Todas as alterações relevantes deste projeto serão documentadas neste ficheiro.

## [Unreleased]

### Alterado

- Diagnóstico estrutural seguro do envelope MQTT para preparar futuras
  consultas Modbus exclusivamente de leitura, sem registar conteúdo,
  identificadores ou credenciais.
- Diagnóstico de interoperabilidade confirmou que os pedidos remotos incluem
  dois valores alfanuméricos variáveis gerados pela cloud. O ensaio de uma
  consulta local foi rejeitado pelo RWB1 e a opção experimental foi retirada
  da configuração para impedir ativação acidental.

### Adicionado

- Proxy MQTT transparente e passivo para o datalogger Solar Plug-RWB1.
- Descodificação dos blocos Modbus RTU confirmados e publicação por MQTT
  Discovery.
- Aplicação para Home Assistant OS com ligação automática ao serviço Mosquitto.
- Mapa de registos com níveis de confiança e matriz de compatibilidade.
- Testes unitários, verificação de sintaxe e CI.

### Segurança

- Credenciais MQTT do dongle nunca são registadas.
- Identificadores específicos do equipamento são ocultados nos tópicos dos
  logs.
- Esta versão não permite injeção de pedidos nem escrita Modbus.
