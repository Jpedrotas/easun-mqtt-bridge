# Segurança

Este projeto observa tráfego MQTT não cifrado que pode conter credenciais e
identificadores únicos. Relatórios públicos nunca devem incluir capturas de rede,
logs integrais, credenciais, endereços MAC, identificadores do datalogger ou
tópicos MQTT completos.

Para comunicar uma vulnerabilidade, não abra uma issue com dados reais. Use o
canal privado de segurança do repositório quando este estiver publicado.

O bridge é deliberadamente passivo: não injeta pedidos e não escreve registos
do inversor. Qualquer futura funcionalidade de controlo deverá ser opcional,
limitada por uma lista de registos permitidos e acompanhada por testes.
