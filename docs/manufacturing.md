# Manufacturing and selling small batches

Reviewed **2026-10-17**. This is a sourcing and pilot plan, not a quotation, sales
forecast or authorization to place an order. Both PCB architectures and all
three delivery formats are in scope. No manufacturer has quoted production
files for this project, and no complete unit has passed physical acceptance.
The machine-readable companion is
[manufacturing-options.json](../hardware/low-power/manufacturing-options.json).

## Six possible products

Keep architecture, delivery format and revision separate in the product name.
Define the included parts before requesting quotations or accepting orders:

- **Modular / bare PCB:** the unpopulated low-voltage backplane and one LP-M0
  MGM240P adapter PCB. Buyers supply SC16 circuitry, keyed connectors,
  harnesses, controller/radio modules and
  power/Ethernet assemblies. Publish exact compatible module revisions and the
  assembly BOM. This is the most accessible DIY starting point, but still
  includes fine-pitch soldering unless that circuitry is supplied separately.
- **Modular / PCBA:** populate and test the backplane's SC16, support circuitry
  and connectors, plus the required LP-M0 adapter with its MGM240P module and
  support circuitry. State explicitly whether harnesses are included. Other
  external radio/host/power modules are excluded unless individually listed;
  a tested backplane/adapter set is not a tested complete hub. Quote other
  module installation as a separate assembly operation.
- **Modular / finished:** install all specified modules, antennas and harnesses
  in an enclosure, load the released firmware and test the complete hub. This
  format takes responsibility for module compatibility, wiring and onboarding.
- **Integrated / bare PCB:** the unpopulated carrier for the S3, H2, MG24,
  W5500/Ethernet and PoE sections. This is an advanced reflow/rework build, not
  a beginner soldering kit. ZAC93, CC1101 and sensors must be listed separately
  as appropriate to the final BOM.
- **Integrated / PCBA:** assemble and test the integrated electronics with an
  explicit installed-module, antenna and sensor list. An operational radio PCBA
  can already be radio equipment even without an enclosure. Do not describe
  an unpopulated sensor header as an included sensor.
- **Integrated / finished:** add the final antennas, radar window, external BME
  pod, enclosure, firmware provisioning and end-to-end test. This has the
  greatest integration and support responsibility.

The current electrical PCB candidates have different manufacturing geometry:

- **LP-C0 modular backplane:** **160 × 100 mm, two copper layers**; isolated
  regulated 5 V input, with the PoE front end and radio/host modules off-board.
- **LP-I0 integrated carrier:** **160 × 142 mm, four copper layers**; on-board
  PoE input, S3/H2/MG24 and W5500 sections, with specified external radios and
  sensors connected by harnesses.

LP-C0 also needs **one LP-M0 MGM240P adapter per modular hub**, currently
**60 × 40 mm, two copper layers**, with a 1.6 mm board and proposed 1 oz copper.
Its module antenna edge aligns with the PCB edge; the width accommodates the
manufacturer's 55–60 mm ground-plane recommendation. Quote it as a separate
PCB/assembly line. A five-hub modular set needs five C0 backplanes and five M0
adapters. LP-I0 mounts the MGM240P directly and does not need LP-M0.

All three PCBs are **engineering prototypes, not fabricated and not released for
production**. These are the current CAD dimensions and layer counts, not a
validated production design. The fabricator's stack-up, controlled-impedance
geometry, copper, isolation review, RF clearances and panelization still need
approval. Prices must be recalculated if either design changes. Do not apply a
two-layer quotation to LP-I0. Neither new board is a drop-in fit in the earlier
concept enclosure; see the [mechanical compatibility review](../hardware/low-power/visual/physical/README.md#enclosure-compatibility-with-the-actual-pcb-candidates).

The [draft RFQ](manufacturing-rfq.md) requests separate 5/10/20-unit quotations
for both designs and all three delivery formats. It has not been sent.

## Where to request 10 and 20 boards

**JLCPCB** is a useful first PCB/PCBA quotation for both designs. Its September
2026 schedule lists Economic assembly setup at **US$8.18**, or Standard
single-sided setup at **US$25.56**; the corresponding stencil charges are
**US$1.53 / US$8.21**. The initial SMT tier is **US$0.0016 per solder joint**.
These are individual charges, not the price of this hub. Parts, PCB fabrication,
extended-part feeders, manual work, fixtures, inspection and freight can add
substantially. Confirm service eligibility and sourcing for each radio, PoE
module and connector in the submitted BOM. [Published assembly charges](https://jlcpcb.com/help/article/pcb-assembly-price),
[assembly and sourcing options](https://jlcpcb.com/pcb-assembly).

**PCBWay** is the parallel quotation, especially for mixed surface-mount,
through-hole and customer-supplied modules. Its published assembly capability
starts at **five pieces**. Request PCB fabrication, assembly, programming,
functional testing and manual module installation as separate lines. It asks
for Gerbers, BOM and centroid data; supply assembly drawings too. Consigned
components need excess quantities, and the exact overage/return policy must be
agreed before sending expensive modules. No project price was obtained.
[Assembly capabilities](https://www.pcbway.com/assembly-capabilities.html),
[assembly order FAQ](https://www.pcbway.com/assembly-faq.html).

**OSH Park** provides a reproducible US bare-board comparison. Its two-layer
Medium Run service publishes **US$1 per square inch per board**, at least
**100 square inches in the order**, with each design in multiples of **10**.
Published fabrication-to-shipment time is 12–21 calendar days, not delivery to
the buyer. For the current **LP-C0 160 × 100 mm, two-layer** outline:

- Area = `160 × 100 / 25.4² = 24.80005 in²`.
- Ten boards: approximately **US$248.00** in board fabrication.
- Twenty boards: approximately **US$496.00** in board fabrication.

Both satisfy the minimum. These calculated examples exclude assembly, parts,
taxes/import charges and any applicable shipping options; they are **not uploaded
Gerber quotations**. This formula applies only to **LP-C0** in this comparison.
It does **not** quote the LP-M0 adapter, the four-layer LP-I0 board or a five-board first article;
request those separately using an eligible service. Recalculate if the LP-C0
outline changes. This is a bare-board option, not the PCBA recommendation.
[OSH Park Medium Run terms](https://docs.oshpark.com/services/two-layer-medium-run/).

**AISLER** is the EU alternative for PCB fabrication and assembly. Beautiful
Boards are supplied in sets of **three**, while Amazing Assembly starts at
**one** and supports through-hole and surface-mount work. Therefore request
12/21 bare boards when comparing against a need for at least 10/20, or ask about
a series offer; request exact quantities for assembly. Use the project upload
for a current price. Its separate series service advertises programming,
testing and box build. [AISLER product and service scope](https://aisler.net/en/products).

For both designs, send the same controlled package to JLCPCB and PCBWay; add
AISLER when EU sourcing/assembly is useful and OSH Park for a bare-board
benchmark. Select after DFM review, parts availability and test scope are clear,
not from an advertised setup minimum.

## A useful quotation and cost model

Prepare a tagged source revision plus Gerber/Excellon files, fabrication drawing,
stack-up, BOM with exact manufacturer part numbers and approved substitutions,
CPL with rotation/origin conventions, assembly drawings, DNP list, panel/tooling
requirements, programming instructions and the acceptance procedure. Identify
customer-supplied parts, moisture-sensitive handling and who owns unused stock.
Request separate prices for 5 first articles, 10 and 20 **of each architecture**;
variants cannot be assumed to share setup or panel costs.

Ask for these lines rather than one opaque total:

- PCB fabrication, stencil, assembly setup/NRE, feeders and minimum charges.
- Components, procurement minimums, consignment overage, manual soldering and
  connector/harness work; who pays for damaged high-value modules.
- Programming, fixture development and ownership, functional-test time,
  rework/retest and the definition of a delivered accepted unit.
- Freight, declared shipping terms, insurance, duties/tax and sample lead time.
- Enclosure/printing, hardware, labels, packaging and final assembly if included.

Use `accepted unit cost = total attributable batch cost / accepted units`,
then add outbound fulfillment, platform/payment fees, support and a replacement
reserve when setting a sale price. Fixed costs spread over 20 units are half
their per-unit amount at 10; parts prices and yield do not automatically improve.
For sensitivity only, compare **100%, 95% and 90% usable yield**: these are
planning assumptions, not measured factory yield. If the vendor contracts to
deliver 10 tested good units, do not also charge the buyer for an assumed
factory scrap factor hidden inside that quote. Count prototypes and retained
spares separately. There is no defensible sale price or profit forecast yet.

## Prototype, pilot 10, then 20

1. **Engineering first articles:** request 5 per architecture, adjusted to the
   service minimum. Complete schematic/layout review and bench bring-up before
   calling these saleable. Compare a fully working specimen of each architecture
   for power, radio coexistence, recovery and serviceability.
2. **Pilot 10:** only release a reviewed revision with a repeatable fixture and
   acceptance record. Allocate at least one retained reference unit and a
   replacement stock allowance explicitly; ten built units need not mean ten
   available to sell. Offer all three formats with clear inclusions, but do not
   manufacture ten of every format merely to fill six catalogue entries.
3. **Follow-on 20:** proceed per architecture only after documented interest at
   the actual delivered price, acceptable first-pilot yield and support effort,
   and no unresolved systemic faults. PCBAs and finished units can share an
   assembly batch only if their hardware BOM is identical and final operations
   remain traceable. A like or poll vote is not a sale commitment.

This project may serve builders who value one Ethernet/PoE connection and the
combined radio functions. That is a product hypothesis, not evidence of demand.
A small, transparent pilot is justified more readily than an inventory purchase
for six unvalidated SKUs.

## Fixture, quality control and support

Use a current-limited isolated supply for secondary-side bring-up, keyed harness
adapters, pogo/service connections, a known-good Ethernet/PoE source and a
dedicated test network. Expose ground/rails, reset/boot, USB/SWD and communication
test points in the design. Keep high-voltage PoE input/isolation tests separate
from ordinary logic probing. Define PoE isolation/production test requirements
with the selected PD design and test provider; a continuity check is insufficient.

For every PCBA, record visual/AOI results, shorts/polarity, rail voltages and
current, programming verification, reset/recovery and each populated interface.
Backplanes need loopback and loaded harness tests. Complete radio assemblies
need actual Zigbee and Thread commissioning/traffic, Z-Wave communication,
CC1101 receive/transmit against a test fixture, BLE discovery, radar and BME
readings, and simultaneous-load/network-loss tests. Respect the region's RF
settings and use an appropriate shielded/conducted test arrangement where needed.
AOI and successful firmware flashing do not prove RF operation.

For finished units add antenna/enclosure inspection, strain relief, repeated
cold starts, thermal and power readings, onboarding and factory-reset tests.
Qualify a longer soak on first articles; choose production soak duration from
observed faults and record it, rather than claiming an unperformed 24-hour test.
Use a serial, PCB revision, BOM variant, firmware hashes, test-script version,
date and pass/fail/rework record. Do not publish customer keys or test-network
credentials. Provision unique credentials or a local first-use setup flow;
never clone the live home configuration into a sale image.

Publish the exact included hardware, regional radio variant, supported HA
integration/firmware versions, setup instructions, tested limitations and a
support contact. Keep replacement units and a known-good fixture. Triage returns
by serial and fault description; reproduce and log the fault, erase credentials
and retest repairs. A DIY label or an MIT software warranty disclaimer does not
replace the seller's product obligations. For EU consumer distance sales, plan
for applicable 14-day withdrawal and at least two-year conformity protection;
country-specific rules and exceptions still matter.
[EU seller guidance](https://europa.eu/youreurope/business/selling-in-eu/consumer-contracts-guarantees/consumer-guarantees/index_en.htm).

## Licenses and sale permissions

The repository's [MIT license](../LICENSE) permits commercial use and sale of
its original code, documentation and CAD, with copyright/license notices
retained. It does not relicense dependencies or grant third-party trademarks.
Use [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) as the release checklist,
not a claim that the entire product is MIT.

Vendored KiCad and Espressif footprint libraries retain **CC BY-SA 4.0 with
the KiCad electronic-design exception**. Preserve their attribution/license
files when redistributing library sources. The exception allows the original
PCB designs and generated design files to retain the project's own license;
it does not relicense the upstream library artwork as MIT. The footprint and
contact-reference directories identify the copied sources.

The shipped ESPHome C++ runtime includes **GPLv3** code. Binary distribution
requires a compliant Corresponding Source route for the actual version shipped,
including modifications and build material; applicable User Product installation
information must also be provided. Preserve the MIT RF Airbridge notices and
the Apache/OpenThread/ESP-IDF notices for included components. The practical
approach is a versioned source-and-license package with each firmware release,
not just a link to a moving upstream branch. Confirm the complete linked image's
license inventory before distributing it.
[Pinned ESPHome license](https://github.com/esphome/esphome/blob/2026.9.1/LICENSE),
[GNU GPL distribution guidance](https://www.gnu.org/licenses/gpl-faq.en.html).

The MG24 NCP uses Simplicity SDK **2025.6.3**. Its license file applies Silicon
Labs' MSLA by default, with file-specific exceptions. The MSLA permits specified
object-code distribution in authorized applications using Silicon Labs devices
and has conditions for external manufacturers/end users; it does not make the
SDK freely redistributable as MIT. Preserve notices and verify the terms
accepted with the pinned SDK before sending manufacturing/programming packages.
Keep this separate-radio image's terms distinct from the S3 GPL source package.
[Pinned SDK license](https://github.com/SiliconLabs/simplicity_sdk/blob/b41bec3ff2485199c1a5a9995b3e649e118c1b8d/License.txt),
[Silicon Labs MSLA, sections 4–7 and 20](https://www.silabs.com/about-us/legal/master-software-license-agreement).

## Radio products: US and EU release boundaries

A genuinely unpopulated PCB is not itself a working intentional radiator.
That observation is not a blanket exemption for a powered backplane, a radio
PCBA or a kit sold as a functional hub. Classify the actual contents and intended
use of each SKU. A bag of parts and the word “kit” do not automatically remove
the obligations applying to the assembled radio product.

**United States:** the personal home-built exception in **47 CFR 15.23** is
limited to non-marketed devices, not built from a kit, in quantities of five or
fewer for personal use. It is not the basis for selling 10–20 hubs. Marketing
rules apply before shipping, including offers for sale; use the applicable
authorization route before a commercial radio launch.
[15.23](https://www.ecfr.gov/current/title-47/chapter-I/subchapter-A/part-15/subpart-A/section-15.23),
[2.803](https://www.ecfr.gov/current/title-47/chapter-I/subchapter-A/part-2/subpart-I/section-2.803).

Modular approvals are conditional on the grant and integration instructions,
including antenna, RF exposure and labeling conditions. Multiple transmitters,
host emissions and the final installation require review. The presence of
approved modules does **not** certify this whole hub; do not assume that every
existing CC1101/radar board has a transferable approval. Obtain a lab's scoped
assessment of the selected module grants, simultaneous transmission and host
digital emissions before selling the radio PCBA/finished variants.
[15.212](https://www.ecfr.gov/current/title-47/chapter-I/subchapter-A/part-15/subpart-C/section-15.212),
[FCC module integration guidance, KDB 996369](https://apps.fcc.gov/oetcf/kdb/forms/FTSSearchResultPage.cfm?id=44637&switch=P).

**European Union:** assess the actual radio product against RED safety, EMC and
spectrum requirements, with technical documentation, conformity assessment,
EU Declaration of Conformity and required identification/instructions/CE marking.
RED's amateur-radio kit and professional R&D evaluation-kit exclusions are
narrow; an ordinary home-automation consumer kit does not inherit them. Approved
modules are evidence for the assessment, not a substitute for the final product's
conformity. Also scope other applicable product/environmental obligations with
the intended market before launch.
[RED articles 2, 3, 10, 17–21 and Annex I](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02014L0053-20241228).

For an Internet-connected hub, include the applicable RED cybersecurity
requirements in that review. The Commission states that Delegated Regulation
2022/30 has applied since August 2025; its repeal takes effect **11 December
2027**, when the CRA's main obligations apply. Do not interpret the announced
repeal as an October 2026 exemption. Plan a maintained update/security contact
and check the rules applicable on the actual sale date.
[European Commission RED and cybersecurity status](https://single-market-economy.ec.europa.eu/sectors/electrical-and-electronic-engineering-industries-eei/radio-equipment-directive-red_en).

## Where to sell, after those gates

**Tindie** remains a candidate, but its seller/terms pages could not be retrieved
in this review. Its current fees, payout access, country support and seller
obligations are **unverified**. Do not budget a historical “5%” as an all-in fee.
Verify directly before opening a listing. [Tindie seller entry](https://www.tindie.com/sell/).

**SmallRun** publishes a maker-marketplace alternative. Its FAQ advertises
**7% of product plus shipping, plus US$0.40 per order**, with card processing
included; its Terms section 4 also describes separate Stripe processing fees.
This inconsistency needs confirmation during onboarding before using that rate
as a contractual cost. Payout method, conversion and hold periods can add cost
or delay. Its Terms require accurate listings and a minimum **30-day** return
window for unused, undamaged, non-personalized goods. The seller remains party
to the sale; the platform is not the hub's manufacturer.
[SmallRun fee FAQ](https://www.smallrun.net/faq),
[SmallRun seller terms](https://www.smallrun.net/terms).

Start with a non-binding interest list and clear prototype evidence, not paid
orders for unvalidated radio hardware. Before choosing a storefront, verify
actual seller onboarding, payout/return terms, tax/import handling and usable
shipping destinations. No platform traffic, conversion rate or buyer demand has
been established for this project.
