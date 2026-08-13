# Compatibilidade observada

## Datalogger

| Campo | Valor |
|---|---|
| Modelo indicado na embalagem | `Solar Plug-RWB1` |
| Tipo indicado na embalagem | `04` |
| Referência comercial observada | `ECOMAX-730-70081-00` |
| Ligação à cloud | MQTT 3.1.1 sobre TCP |
| Encapsulamento do inversor | JSON com frames Modbus RTU em Base64 |
| Estado do teste | Proxy transparente validado, mantendo a aplicação do fabricante |

## Inversor

O equipamento usado na validação é um EASUN iSolar SMH III 4,2 kW. A
compatibilidade com outras potências, versões de firmware ou revisões do RWB1
não deve ser assumida sem capturas e validação adicionais.

## Privacidade

IDs, números de série, endereços MAC, QR codes e identificadores MQTT do
equipamento de teste não fazem parte deste repositório.
