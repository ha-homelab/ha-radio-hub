#!/usr/bin/env python3
"""MC2-D S1 assembly legend. Only F.SilkS/B.SilkS artwork is changed.

Coordinates are front-view millimetres, including back-side text (mirrored by
KiCad). The QR uses unprinted dark mask on a white field, with four light
modules of quiet zone. No copper, mask, drill, component or net is added.
"""
import json
from pathlib import Path
import pcbnew as pcb

ROOT = Path(__file__).resolve().parent
REVISION = 'S1'


def apply(board):
    layers = {pcb.F_SilkS, pcb.B_SilkS}
    # Replace board-level legends; retain native passive/header body outlines.
    for item in list(board.GetDrawings()):
        if item.GetLayer() in layers:
            board.RemoveNative(item)
    for fp in board.GetFootprints():
        if fp.Reference().GetLayer() in layers:
            fp.Reference().SetVisible(False)
        for item in list(fp.GraphicalItems()):
            if item.GetLayer() in layers:
                if hasattr(item, 'GetText') or fp.GetReference().startswith('U'):
                    fp.RemoveNative(item)
                elif item.GetWidth() < pcb.FromMM(.15):
                    item.SetWidth(pcb.FromMM(.15))

    def point(x, y):
        return pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y))

    def text(value, x, y, size=1, back=False, angle=0):
        t = pcb.PCB_TEXT(board)
        t.SetText(value)
        t.SetPosition(point(x, y))
        t.SetTextSize(point(size, size))
        t.SetTextThickness(pcb.FromMM(.15))
        t.SetLayer(pcb.B_SilkS if back else pcb.F_SilkS)
        t.SetMirrored(back)
        t.SetTextAngle(pcb.EDA_ANGLE(angle, pcb.DEGREES_T))
        board.Add(t)

    def line(x1, y1, x2, y2, back=False, width=.15):
        s = pcb.PCB_SHAPE()
        s.SetShape(pcb.SHAPE_T_SEGMENT)
        s.SetStart(point(x1, y1))
        s.SetEnd(point(x2, y2))
        s.SetWidth(pcb.FromMM(width))
        s.SetLayer(pcb.B_SilkS if back else pcb.F_SilkS)
        board.Add(s)

    def rect(x1, y1, x2, y2, filled=False):
        s = pcb.PCB_SHAPE()
        s.SetShape(pcb.SHAPE_T_RECT)
        s.SetStart(point(x1, y1))
        s.SetEnd(point(x2, y2))
        s.SetWidth(0 if filled else pcb.FromMM(.15))
        s.SetFilled(filled)
        s.SetLayer(pcb.F_SilkS)
        board.Add(s)

    text('HA RADIO HUB', 50, 4.5, 2)
    text('MC2-D  /  S1 SILK  /  100 x 100 mm', 50, 7.3, .9)
    for x1, x2 in [(7, 32), (68, 93)]:
        line(x1, 4.5, x2, 4.5, width=.25)
    # Module outlines follow the body ledger; no invented holes or footprints.
    design = json.loads((ROOT / 'design.json').read_text())
    parts = {p['ref']: p for p in design['parts']}
    for ref in ('U1', 'U2', 'U3', 'U4'):
        x1, y1, x2, y2 = parts[ref]['body_bounds_global_mm']
        rect(x1, y1, x2, y2)
    for label, x, y in [('U1  HOST / BLE', 22, 10),
                        ('U2  THREAD', 53.8, 10),
                        ('U3  ZIGBEE', 83.9, 10),
                        ('U4  ETHERNET', 70.5, 72.6)]:
        text(label, x, y)
    for value, x, y, size in [
        ('ESP32', 22, 32, 1.7), ('DevKitC-VIE', 22, 35, 1.3),
        ('WROVER-IE', 22, 38, 1.1), ('HOST + BLE PROXY', 22, 43, 1),
        ('ESP-NOW READY', 22, 46, 1), ('38 PINS / 25.40 mm', 22, 51, .85),
        ('USB: LOOSE BOARD ONLY', 22, 61, .8),
        ('XIAO', 57.8, 22, .85), ('C6', 57.8, 24, .85),
        ('XIAO MG24', 83.9, 21, 1.1), ('ZIGBEE NCP', 83.9, 24, .9),
        ('WIZ850io', 70.5, 82, 1.3), ('3V3 ONLY', 70.5, 85, 1),
        ('RJ45 OUT', 70.5, 96, 1),
        ('CONNECT 3 x 2.4 GHz ANTENNAS', 23, 69.5, .8),
    ]:
        text(value, x, y, size)
    # Host UART net names describe the remote peripheral's TX/RX endpoints.
    # Physical pin labels use direction-neutral nets on front and full names
    # on the back. Never infer harness order from wire colour.
    headers = {
        'J1': ('5V INPUT / FUSED', ['5V', 'GND']),
        'J2': ('RECOM / OFFBOARD', ['5V', 'GND', '3V3', 'GND']),
        'J3': ('DFR0627 / UART', ['3V3', 'GND', 'SDA', 'SCL', 'ZRX', 'ZTX']),
        'J4': ('ZAC93 / Z-WAVE', ['3V3', 'GND', 'GND', 'ZRX', 'ZTX']),
        'J5': ('CC1101 / RF', ['3V3', 'GND', 'SCK', 'MOSI', 'MISO', 'CS', 'GD0', 'GD2']),
        'J6': ('LD2450 / RADAR', ['5V', 'GND', 'RX', 'TX']),
        'J7': ('BME680 / I2C', ['GND', '3V3', 'SDA', 'SCL']),
        'J10': ('C6 RECOVERY', ['EN', 'BOOT']),
    }
    for ref, (role, labels) in headers.items():
        pads = parts[ref]['pad_centers_mm']
        cx = (pads[0]['x'] + pads[-1]['x']) / 2
        y = pads[0]['y']
        text(ref + ' ' + role, cx, y - 2.7, .8)
        for pad, label in zip(pads, labels):
            text(label, pad['x'], y + (2.1 if ref == 'J1' else 3.2), .8,
                 angle=0 if ref == 'J1' else 90)
        text('1', pads[0]['x'] - 2.3, y, .9)
        # Back labels are mirrored in native CAD, so they read
        # correctly when the physical board is turned over for soldering.
        text(ref + ' ' + role, cx, y - 2.8, .8, back=True)
        for pad, label in zip(pads, labels):
            text(label, pad['x'], y + (2.1 if ref == 'J1' else 3.2),
                 .8, back=True, angle=0 if ref == 'J1' else 90)
        text('1', pads[0]['x'] - 2.3, y, .9, back=True)

    for ref, value in [('R1', '4K7'), ('R2', '10K'), ('R4', '10K'), ('R5', '10K')]:
        x, y = parts[ref]['xy']
        text(ref + ' ' + value, x + 3.81, y - 2.2, .85)
    for ref, dest in [('D2', 'C6'), ('D3', 'MG24')]:
        x, y = parts[ref]['xy']
        text(ref + ' 1N5819', x + 3.81, y - 2.4, .8)
        text('K', x - 2, y, .8)
        text('K -> ' + dest, x + 3.81, y + 2.8, .8)
    text('D1  WIRE LINK', 43.81, 92, .85)
    text('22 AWG / NO DIODE', 43.81, 97, .8)
    text('J8 MG24 BOOT', 90, 80, .8)
    text('J9 HOST BOOT', 89.8, 89.2, .8)
    text('LEAVE OPEN', 90, 88, .8)
    text('LEAVE OPEN', 89.8, 95, .8)

    # Bottom side assembly checklist occupies the space inside U1 header rows.
    for i, value in enumerate([
        'ASSEMBLY NOTES', 'SOLDER FROM THIS SIDE', '1. CHECK BARE RAILS',
        '2. R1 / R2 / R4 / R5', '3. D1 = WIRE LINK', '4. D2 / D3 BAND = K',
        '5. C6 TP8=EN TP2=BOOT', '6. HEADERS + MODULES',
        'R3: DO NOT FIT', 'J8 / J9: LEAVE OPEN',
        'NO POWERED USB', 'ON ASSEMBLED HUB', '5V FUSED INPUT ONLY',
        'CHECK RAILS + POLARITY', 'BEFORE FIRST POWER',
    ]):
        text(value, 22, 21 + 2.7 * i, .85 if i else 1.1, back=True)
    text('HA RADIO HUB / MC2-D / S1', 55, 5, 1.5, back=True)
    text('BOTTOM VIEW - PIN 1 IS SQUARE', 55, 8, 1, back=True)
    text('C6: TP8 EN / TP2 BOOT', 54, 35, .8, back=True)
    text('RF: GD0=GDO0 GD2=GDO2', 48, 47, .8, back=True)
    text('ZRX / ZTX = ZWAVE_RX / TX', 79, 63, .8, back=True)
    text('RECOM: 5V IN -> 3V3 OUT', 70, 76, .85, back=True)
    text('U4 WIZ850io', 70, 83, 1, back=True)
    text('3V3 / ETHERNET', 70, 86, .85, back=True)
    text('NO RAW PoE HERE', 70, 96, .85, back=True)

    qr = json.loads((ROOT / 'silkscreen-qr.json').read_text())
    m = qr['module_mm']
    x0, y0 = 8, 82
    for row, cells in enumerate(qr['matrix']):
        # Coalesce white modules horizontally; no ink on dark modules.
        start = None
        for col in range(len(cells) + 1):
            light = col < len(cells) and cells[col] == '0'
            if light and start is None:
                start = col
            elif not light and start is not None:
                rect(x0 + start*m, y0 + row*m, x0 + col*m,
                     y0 + (row+1)*m, filled=True)
                start = None
    text('SCAN BUILD GUIDE', 29.3, 89.5, .8, angle=90)


if __name__ == '__main__':
    path = ROOT / 'mc2.kicad_pcb'
    board = pcb.LoadBoard(str(path))
    apply(board)
    pcb.SaveBoard(str(path), board)
    from project_rules import restore_project_rules
    restore_project_rules()
