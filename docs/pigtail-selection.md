# MC2-C pigtail selection

Checked **19 October 2026** for one prototype delivered to the United States.
Buy **3 × Taoglas CAB.618.E**, one each for BLE, Thread and Zigbee. Keep the
three **TE/Linx ANT-2.4-LCW-SMA** antennas. This replaces the previously selected
Amphenol cables without changing the carrier PCB or radio firmware. Use the
matching **FH1-MC2-C-PWR1** enclosure and connector coupon.

## Exact part and observed cost

[DigiKey 931-CAB.618.E-ND](https://www.digikey.com/en/products/detail/taoglas-limited/CAB-618-E/26766261)
showed **48 in stock** and **$4.66 each**, so three cost **$13.98** before
shipping, tax and any tariff. Against the previous $29.47-per-cable offer,
the reduction is **$74.43 for one hub** ($88.41 → $13.98, about 84%).
This is an observed offer, not reserved stock or a checkout total; DigiKey
specifically states that a US tariff may appear in the cart.

The [Taoglas product page](https://www.taoglas.com/product/cab-618-e-i-pex-mhf-i-u-fl-to-150mm-1-13mm-coax-black-cable-smaf-bulkhead-straight/)
identifies a **150 mm, 1.13 mm micro-coax** assembly with a right-angle
**I-PEX MHF I / U.FL-compatible** radio connection and a straight
**standard-polarity SMA female bulkhead**. The SMA end has a center socket;
the selected antenna has the mating center pin. Do not substitute RP-SMA
or the smaller MHF4/IPEX4 connector.

## Why this cable

| Candidate | Observed unit price | Availability | Decision |
| --- | ---: | --- | --- |
| [Taoglas CAB.618.E](https://www.digikey.com/en/products/detail/taoglas-limited/CAB-618-E/26766261) | $4.66 | 48 at DigiKey | Selected: stated nominal length and connector family; published family drawing and cable-type specification support the RF1 design |
| [GCT CABLE 348 RF-150-A-1](https://www.digikey.com/en/products/detail/gct/CABLE-348-RF-150-A-1/12822383) | $2.93 | 318 at DigiKey | Research candidate: matching basic connector family and nominal length, but its bulkhead and complete routing have not been qualified for RF1 |
| [SparkFun WRL-18568](https://www.sparkfun.com/sma-to-u-fl-cable-150mm.html) | $2.75 | In stock | Less expensive; its checked product documentation does not provide the same dimensional and RF evidence |
| [Adafruit 851](https://www.adafruit.com/product/851) | $3.95 | In stock | Product description says SMA, but its linked drawing labels RP-SMA; this conflicting evidence prevents qualification |

The alternatives may work, but they are not the released enclosure's selected
assembly. Savings alone do not establish that a different bulkhead, nut or cable
will fit. The existing unverified AliExpress offers remain sample candidates.
In particular, Adafruit's
[linked C934-001 drawing](https://cdn-shop.adafruit.com/product-files/851/C934-001_datasheet.pdf)
labels both “SMA Female RP” and “RP - SMA Female”. That conflicts with the
standard-SMA product description; it is not proof that the item actually
shipped has reverse polarity.

## RF evidence and its limits

Taoglas publishes a
[1.13 mm black micro-coax specification](https://cdn.taoglas.com/specifications/30021F0020000A_Taoglas.pdf)
with **50 ±3 Ω**, **6.8 mm minimum bend radius**, and attenuation of
**3.1 dB/m at 2400 MHz**. RF1 uses these cable-type values as its engineering
basis; the checked sources do not prove that this exact wire part is used
in every CAB.618.E manufacturing lot. Multiplying by the nominal 0.150 m gives an
estimated **0.465 dB cable-only loss**. This excludes both connectors,
mismatch and assembly variation; it is not a measured insertion-loss result
for the complete CAB.618.E or this hub.

Manufacturer geometry references are the
[cable assembly catalog, CAB.618.E drawing on PDF page 11](https://www.taoglas.com/datasheets/Taoglas_Cable_Assembly_Catalog.pdf)
and a [published CAB.618.E STEP link](https://www.taoglas.com/assets/3d-models/CAB.618.E_Web.STEP).
The STEP download was blocked and was not inspected; no dimensions were taken from it.
The catalog groups the 150 mm CAB.618.E with several cable lengths, but its
shared drawing labels **200 ±6 mm**. It does **not** establish an exact
150 mm length tolerance. The project therefore reserves a **6 mm shortfall
allowance**, giving a **144 mm minimum design budget**. This is a conservative
engineering assumption, not a supplier guarantee; check the received cable.

The same family drawing specifies a **14.8 ±0.3 mm** SMA body, **11.4 ±0.3 mm**
threaded portion, **1.75 ±0.2 mm** nut and **1.1 ±0.3 mm** washer, with a
**1/4-36 UNS-2A** thread. These dimensions support the enclosure review,
while the final nut position and antenna engagement must be checked physically.
RF1 provides **6.8 mm round bulkhead holes** and a coupon with the same
**3 mm mounting thickness** as the enclosure. Its routing reserves
**25 mm service slack within the 144 mm design budget**.
Use the current [full-hub assembly instructions](full-hub-assembly.md), connector
coupon and generated fit report for the corresponding mounting and routing.
Do not mix an older coupon or routing illustration with the new cable.

Before closing the first enclosure, check the delivered cable against its
specified dimensions, mount the bulkhead without twisting the micro-coax,
and confirm that the cable reaches with service slack and bends no tighter
than 6.8 mm radius. Seat each miniature connector squarely; leave no tension
on the radio socket. Confirm usable antenna engagement with the supplied
washer and nut. The drawing review does not replace this first-article fit
check or an in-home BLE/Thread/Zigbee coverage test.

See the [radio shopping list](mc2-shopping.md) for the remaining radio parts
and the [PCB ordering guide](pcb-order.md) for the unchanged MC2-C Gerbers.
