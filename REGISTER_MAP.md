# Register map

This map applies to the EASUN iSolar SMH III 4.2 kW inverter observed through an
RWB1 datalogger. The protocol is Modbus RTU with slave address `5`, function
`03` for reads, and function `06` for writes. Sixteen-bit response values use
little-endian byte order.

## Confirmed telemetry

The periodic 21-word block maps to registers 4501–4521. Its relationship with
the PowMr/Sumry family is supported by the block address, format, byte order,
and observed physical values.

| Address | Hex | Field | Scale | Confidence |
|---:|---:|---|---:|---|
| 4501 | `0x1195` | Status/mode code | 1 | high |
| 4502 | `0x1196` | Grid voltage | 0.1 V | high |
| 4503 | `0x1197` | Grid frequency | 0.1 Hz | high |
| 4504 | `0x1198` | PV voltage | 0.1 V | high |
| 4505 | `0x1199` | PV power | 1 W | high |
| 4506 | `0x119A` | Battery voltage | 0.1 V | high |
| 4507 | `0x119B` | Battery state of charge | 1% | high |
| 4508 | `0x119C` | Battery charge current | 1 A | high |
| 4509 | `0x119D` | Battery discharge current | 1 A | high |
| 4510 | `0x119E` | Output/load voltage | 0.1 V | high |
| 4511 | `0x119F` | Output/load frequency | 0.1 Hz | high |
| 4512 | `0x11A0` | Load apparent power on this revision | 1 VA | medium |
| 4513 | `0x11A1` | Load active power on this revision | 1 W | medium |
| 4514 | `0x11A2` | Load percentage | 1% | high |
| 4521 | `0x11A9` | Rated power | 1 W | high |

Registers 4512 and 4513 are labelled in the opposite order by some older PowMr
projects. On the observed inverter, the values were physically consistent as
595 VA and 462 W. They remain marked as medium confidence until a direct
comparison with the display or vendor app is completed.

## Settings confirmed by captures

Do not blindly reuse write maps from older PowMr models. The observed SMH III
uses a different revision in this range. These registers are documented for
interoperability research only; this bridge does not implement writes.

| Address | Hex | Field | Observed values | Confidence |
|---:|---:|---|---|---|
| 5004 | `0x138C` | LCD backlight | `0`/`1` | high |
| 5017 | `0x1399` | Charging source priority | enumeration | high |
| 5031 | `0x13A7` | Maximum total charge current | ampere | high |
| 5032 | `0x13A8` | Maximum solar charge current | ampere | medium |
| 5036 | `0x13AC` | LED pattern | observed `0`/`1` | high |

## Compatibility references

- SolarAssistant identifies EASUN SMH III 3.6/4.2/6.2 kW devices as using the
  **Sumry** protocol.
- `odya/esphome-powmr-hybrid-inverter` documents the same Modbus slave,
  little-endian response values, and blocks starting at `0x1196`/`0x11BC`.
- `leodesigner/powmr_comm` contains the exact request
  `05 03 13 99 00 01 51 25`, also observed in a real capture.

External projects are interoperability references only; this proxy contains no
source code copied from them.

Exact upstream revisions, standards, and the distinction between public
references and private primary evidence are documented in
[`SOURCES.md`](SOURCES.md).
