# Mapa de registos

Este mapa aplica-se ao EASUN iSolar SMH III 4,2 kW observado através do
datalogger RWB1. O protocolo é Modbus RTU, escravo `5`, função `03` para leitura
e função `06` para escrita. Os valores de resposta de 16 bits usam os bytes em
ordem little-endian.

## Telemetria confirmada

O bloco periódico de 21 palavras corresponde aos registos 4501–4521. A
correspondência com a família PowMr/Sumry é confirmada pelo endereço do bloco,
formato, ordem dos bytes e valores físicos observados.

| Endereço | Hex | Campo | Escala | Confiança |
|---:|---:|---|---:|---|
| 4501 | `0x1195` | Código de estado/modo | 1 | alta |
| 4502 | `0x1196` | Tensão da rede | 0,1 V | alta |
| 4503 | `0x1197` | Frequência da rede | 0,1 Hz | alta |
| 4504 | `0x1198` | Tensão fotovoltaica | 0,1 V | alta |
| 4505 | `0x1199` | Potência fotovoltaica | 1 W | alta |
| 4506 | `0x119A` | Tensão da bateria | 0,1 V | alta |
| 4507 | `0x119B` | Estado de carga da bateria | 1 % | alta |
| 4508 | `0x119C` | Corrente de carga da bateria | 1 A | alta |
| 4509 | `0x119D` | Corrente de descarga da bateria | 1 A | alta |
| 4510 | `0x119E` | Tensão de saída/carga | 0,1 V | alta |
| 4511 | `0x119F` | Frequência de saída/carga | 0,1 Hz | alta |
| 4512 | `0x11A0` | Potência aparente da carga nesta revisão | 1 VA | média |
| 4513 | `0x11A1` | Potência ativa da carga nesta revisão | 1 W | média |
| 4514 | `0x11A2` | Percentagem de carga | 1 % | alta |
| 4521 | `0x11A9` | Potência nominal | 1 W | alta |

Os registos 4512 e 4513 aparecem com os nomes trocados em alguns projetos
PowMr antigos. No equipamento observado, os valores eram fisicamente coerentes
como 595 VA e 462 W; ficam marcados com confiança média até comparação direta
com o ecrã ou a aplicação.

## Configurações confirmadas por captura

Não se deve reutilizar cegamente o mapa de escrita de modelos PowMr antigos. O
SMH III possui uma revisão diferente neste intervalo.

| Endereço | Hex | Campo | Valores observados | Confiança |
|---:|---:|---|---|---|
| 5004 | `0x138C` | Luz de fundo do LCD | `0`/`1` | alta |
| 5017 | `0x1399` | Prioridade da fonte de carregamento | enumeração | alta |
| 5031 | `0x13A7` | Corrente máxima total de carga | ampere | alta |
| 5032 | `0x13A8` | Corrente máxima de carga solar | ampere | média |
| 5036 | `0x13AC` | Padrão dos LED | `0`/`1` observado | alta |

## Fontes de compatibilidade

- SolarAssistant identifica o EASUN SMH III 3,6/4,2/6,2 kW como protocolo
  **Sumry**.
- `odya/esphome-powmr-hybrid-inverter` documenta o mesmo escravo Modbus,
  little-endian e blocos iniciados em `0x1196`/`0x11BC`.
- `leodesigner/powmr_comm` contém o pedido exato
  `05 03 13 99 00 01 51 25`, também observado na captura real.

Os projetos externos servem como referência de compatibilidade; o proxy não
inclui código copiado desses projetos.
