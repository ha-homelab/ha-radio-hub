# Draft RFQ: HA Radio Hub prototype PCBs and assembly

<!-- MC1-CURRENT-DESIGN -->
> **Current build: [MC1 — one finished-module carrier](module-carrier.md).** This page retains the earlier design or evaluation for reference. Its board images, pin maps, enclosure fit and alternative BOMs are not the current MC1 build.

This RFQ is retained for the old C0/M0 and I0 designs; do not send it as an MC1 specification. The active [MC1 BOM](../hardware/module-carrier/cad/BOM.csv), [native CAD](../hardware/module-carrier/cad/README.md) and [cost review](../hardware/module-carrier/cost-review/README.md) define the current single-board prototype scope.

**Unsent draft, 2026-10-17.** Intended recipients: JLCPCB and PCBWay, separately.
This is a request for itemized engineering quotations, not an order, a production
release or permission to substitute components. Both designs are prototypes
that have not been fabricated. No customer data or live network credentials
are included.

## Request

Please quote **5, 10 and 20 accepted units of each design**, separately. If a
service has a different minimum, identify the minimum and provide it as an
alternative. Do not combine the two designs into one setup or panel price
unless you also show separate prices.

- **LP-C0 modular backplane:** 160 x 100 mm, 2 copper layers. Low-voltage 5 V
  input; SC16IS752, supervisor, crystal, passives, fuse and keyed connectors
  on the board. Host/radio modules, Ethernet and the isolated PoE power front
  end are separate assemblies. There is no 48 V PoE input on this backplane.
  Include **one LP-M0 MGM240P adapter per LP-C0** as a separate priced line:
  60 x 40 mm, 2 copper layers, proposed 1.6 mm thickness and 1 oz copper,
  MGM240PA22VNA3 module, support parts and two keyed connectors. The quoted
  5/10/20 modular sets therefore need 5/10/20 C0 boards and the same number
  of M0 adapters, not a single shared adapter.
- **LP-I0 integrated carrier:** 160 x 142 mm, 4 copper layers. S3-WROOM-1,
  H2-MINI-1 and MGM240P modules, W5500, PoE MagJack, Ag97005-FL PD module,
  D24V22F3 regulator, UART support circuitry and connectors. ZAC93, CC1101,
  radar and BME680 assemblies remain explicitly listed external items.
  PoE primary/secondary isolation and mixed SMT/through-hole assembly need
  specific DFM review.

Please price three delivery formats for each quantity/design:

1. **Bare PCB:** electrically tested boards only, including the C0/M0 pair
   for each modular set. Quote the chosen surface
   finish, stack-up, copper, board thickness and manufacturing tolerances.
2. **PCBA:** board plus the approved assembly BOM, programming and agreed
   board-level functional testing. Itemize through-hole/module soldering,
   optional harnesses and any external modules. Identify excluded parts.
   For the modular set include the populated M0/MGM240P assembly; other
   off-board modules remain separate explicitly priced options.
3. **Finished prototype hub:** the specified complete module set, harnesses,
   antennas, sensors, final assembly, firmware, labels, packaging and agreed
   full-system tests. The enclosure is still being revised: quote available
   box-build services and engineering NRE now, and mark the enclosure and
   final unit price **pending released mechanical files**. Do not price the
   previous concept STL as a verified fit for either PCB.

## Controlled package to attach before a binding quotation

Provide the exact revision and SHA256 manifest of Gerber/Excellon outputs,
fabrication drawing, assembly drawing, BOM with full manufacturer ordering
codes, DNP/substitution list and CPL. The current PCB source and schematic
are available for review; manufacturing outputs must be regenerated from
the approved revision. Incomplete ordering codes are quotation questions,
not authorization to choose electrically similar parts.

For LP-I0, propose a four-layer stack-up and confirm 90-ohm USB and 100-ohm
Ethernet differential requirements before final trace geometry is released.
Review PoE insulation spacing, slots/keep-outs, module mounting, exposed-pad
paste/thermal-via treatment and assembly sequence. Do not infer regulatory
approval or complete isolation qualification from a passing DRC.

Programming images, versioned build/source-license package, service-pin
drawings and a test specification will accompany the approved assembly
release. Factory test keys must be disposable; no production unit may receive
the home installation's secrets. State how unique credentials or first-use
provisioning will be handled.

## Please itemize and answer

- PCB cost, stencil, setup/NRE, feeders, sourcing/minimum order costs,
  component stock/lead times, hand assembly and programming.
- Fixture design/ownership, test time, inspection/AOI, rework/retest,
  first-article approval and accepted-unit criteria. Quote fixtures/NRE
  separately from recurring unit prices.
- Whether modules may be turnkey or consigned; required overage for each
  high-value item; responsibility for damaged parts; return of unused stock.
- Board-level test coverage: shorts/polarity, loaded rails, reset, UART/SPI,
  Ethernet and programming verification. Complete-hub testing additionally
  needs actual RF traffic, sensors, network/power recovery and thermal checks;
  flashing or AOI alone is insufficient.
- Lead time from approved files/parts, quote validity, currency, payment
  terms, shipping method/Incoterm and separate freight/insurance. Destination
  postal code and applicable import/tax treatment will be supplied before
  the final quotation; do not assume free shipping or tax exemption.
- Manufacturing warranty, treatment of failed acceptance units and RMA
  terms. Identify whether a price is for raw assembled quantity or accepted
  good units, so yield is not counted twice.

Please return DFM questions and conditional estimates first. Fabrication and
assembly may proceed only after a separate approved release/order. The planned
sequence is five engineering first articles, then a conditional ten-unit pilot,
then twenty only after test results and demand justify it. Quantities are
alternatives, not a request to manufacture all formats simultaneously.
