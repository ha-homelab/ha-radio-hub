#!/usr/bin/env python3
"""Independent read-only audit of the Nano MC1 native KiCad board.

Does not import the CAD generator, its ledger, or its assertions. The endpoint
groups below come from the selected firmware contract and manufacturer header
pin maps. Native DRC still owns routed continuity; this audit owns assignment,
module hole geometry, supply boundaries and evidence-file consistency.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCES = {
    "nano": "https://files.waveshare.com/wiki/ESP32-S3-Nano/ESP32-S3-Nano-Schematic.pdf",
    "h2": "https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32h2/esp32-h2-devkitm-1/user_guide.html",
    "xiao": "https://files.seeedstudio.com/wiki/XIAO_MG24/Getting_Start/XIAO_MG24_v1.0_KiCad_260114.zip",
    "wiz": "https://docs.wiznet.io/Product/Modules/Ethernet-Modules/WIZ850io",
}
REAR_REFS = {"U4", *(f"J{i}" for i in range(1, 8)), "D1", "D2", "D3", "R1", "R2"}
SOLDER_ACCESS_RADIUS_MM = 2.0
MIN_COPPER_EDGE_CLEARANCE_MM = 0.5
USB_SHELL_BOUNDS = {
    "U1": [2, -5.81, 13.24, -3.81],
    "U2": [-1.27, 46.685, 24.13, 47.685],
    "U3": [3.12, -5.921, 12.12, -2.921],
}
# Source drawing body bounds, distinct from the larger native courtyards.
MODULE_BODY_BOUNDS = {
    "U1": [-1.27, -3.81, 16.51, 39.37],
    "U2": [-1.27, -1.575, 24.13, 46.685],
    "U3": [-1.27, -2.921, 16.51, 18.034],
    "U4": [-1.34, -6.4, 21.66, 18.6],
}
RAIL_LANDS = {"left": [0, 15, 0.85, 54.5], "right": [46.3, 8, 47.5, 74]}
# These deliberately exceed the contact lands; no copper or exposed via may
# become a high spot beneath a printed ledge on either face.
RAIL_COPPER_EXCLUSIONS = [[0, 14.7, 1.3, 54.8], [46, 7.7, 47.5, 74.3]]
RAIL_MARGIN_MM = 0.3
SOLDER_FILLET_ALLOWANCE_MM = 0.5  # An inspection envelope, not a measured fillet.


def sexpr(text):
    root, stack = None, []
    for token in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text):
        if token == "(":
            node = []
            if stack:
                stack[-1].append(node)
            elif root is not None:
                raise ValueError("Multiple S-expression roots")
            else:
                root = node
            stack.append(node)
        elif token == ")":
            if not stack:
                raise ValueError("Unmatched closing parenthesis")
            stack.pop()
        else:
            if not stack:
                raise ValueError("Atom outside S-expression")
            stack[-1].append(json.loads(token) if token.startswith('"') else token)
    if stack or root is None:
        raise ValueError("Incomplete S-expression")
    return root


def children(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]


def one(node, key, default=None):
    items = children(node, key)
    if len(items) > 1:
        raise ValueError(f"Expected one {key}, got {len(items)}")
    return items[0][1:] if items else default


def read_board(path):
    root = sexpr(path.read_text())
    if root[0] != "kicad_pcb":
        raise ValueError("Not a KiCad PCB")
    parts = {}
    for fp in children(root, "footprint"):
        ref = next((x[2] for x in children(fp, "property") if x[1] == "Reference"), None)
        if not ref or ref in parts:
            raise ValueError(f"Missing or duplicated reference {ref}")
        pos = one(fp, "at")
        pads = {}
        for p in children(fp, "pad"):
            number = p[1]
            if number in pads:
                raise ValueError(f"Duplicate {ref}.{number}")
            pads[number] = {
                "kind": p[2], "at": list(map(float, one(p, "at")[:2])),
                "shape": p[3], "angle": float(one(p, "at")[2]) if len(one(p, "at")) > 2 else 0.0,
                "size": list(map(float, one(p, "size"))),
                "drill": float(one(p, "drill")[0]),
                "net": (one(p, "net") or [""])[-1],
                "type": (one(p, "pintype") or [""])[0],
                "layers": one(p, "layers") or [],
                "uuid": (one(p, "uuid") or [""])[0],
            }
        courtyard = []
        for key in ("fp_rect", "fp_line", "fp_poly"):
            for shape in children(fp, key):
                if one(shape, "layer") != ["B.CrtYd" if one(fp, "layer") == ["B.Cu"] else "F.CrtYd"]:
                    continue
                if key == "fp_rect":
                    x1, y1 = map(float, one(shape, "start"))
                    x2, y2 = map(float, one(shape, "end"))
                    points = [["xy", x, y] for x, y in ((x1,y1),(x2,y1),(x2,y2),(x1,y2))]
                else:
                    points = (one(shape, "pts") if key == "fp_poly" else
                              [["xy", *one(shape, "start")], ["xy", *one(shape, "end")]])
                courtyard.extend([list(map(float, p[1:])) for p in points if p[0] == "xy"])
        parts[ref] = {"name": fp[1], "layer": one(fp, "layer")[0],
                      "at": list(map(float, pos)), "pads": pads,
                      "dnp": "dnp" in (one(fp, "attr") or []),
                      "uuid": (one(fp, "uuid") or [""])[0],
                      "courtyard_local_points": courtyard}
    return parts


def board_bounds(path):
    root = sexpr(path.read_text())
    points = []
    for key in ("gr_rect", "gr_line"):
        for shape in children(root, key):
            if one(shape, "layer") == ["Edge.Cuts"]:
                for endpoint in ("start", "end"):
                    points.append(list(map(float, one(shape, endpoint))))
    if not points:
        raise ValueError("No rectangular/linear native board edge")
    return [min(p[0] for p in points), min(p[1] for p in points),
            max(p[0] for p in points), max(p[1] for p in points)]


def board_outline(path):
    """Read one closed straight-sided native outline; reject unknown geometry."""
    root = sexpr(path.read_text())
    segments = []
    for shape in root:
        if not isinstance(shape, list) or not shape or not shape[0].startswith("gr_"):
            continue
        if one(shape, "layer") != ["Edge.Cuts"]:
            continue
        if shape[0] == "gr_line":
            segments.append([tuple(map(float, one(shape, endpoint))) for endpoint in ("start", "end")])
        elif shape[0] == "gr_rect":
            x1,y1 = map(float, one(shape, "start")); x2,y2 = map(float, one(shape, "end"))
            corners = [(x1,y1),(x2,y1),(x2,y2),(x1,y2)]
            segments.extend(zip(corners,corners[1:]+corners[:1]))
        else:
            raise ValueError("Unsupported native outline primitive " + shape[0])
    if not segments:
        raise ValueError("Missing native outline")
    first = segments.pop(0)
    polygon = [first[0], first[1]]
    while segments:
        matches = [(i, side) for i, ends in enumerate(segments) for side in (0,1)
                   if math.dist(ends[side],polygon[-1]) < 1e-5]
        if len(matches) != 1:
            raise ValueError("Outline has disconnected or branched edges")
        i, side = matches[0]
        polygon.append(segments.pop(i)[1-side])
    if math.dist(polygon[0],polygon[-1]) > 1e-5:
        raise ValueError("Open native outline")
    return polygon[:-1]


def audit_pad_containment(parts, bounds, outline=None):
    errors = []
    for ref in PIN_SETS:
        fp = parts.get(ref)
        if fp is None:
            continue
        x, y, *angles = fp["at"]
        angle = math.radians(angles[0] if angles else 0)
        for number, p in fp["pads"].items():
            px, py = p["at"]
            gx = x + px * math.cos(angle) + py * math.sin(angle)
            gy = y - px * math.sin(angle) + py * math.cos(angle)
            # All current PTH copper pads fit inside a square of this half-width.
            radius = max(p["size"]) / 2
            if min(gx-radius-bounds[0], gy-radius-bounds[1],
                   bounds[2]-gx-radius, bounds[3]-gy-radius) < -0.001:
                errors.append(f"{ref}:{number} copper pad extends beyond board edge")
            if outline is not None:
                if p.get("shape") == "circle":
                    gap = polygon_boundary_distance((gx,gy),outline)-radius
                    inside = point_polygon_distance((gx,gy),outline) <= 0.001
                else:
                    # Bounding rectangle is conservative for roundrect/oval pads.
                    halfx,halfy = (v/2 for v in p["size"])
                    poly = transformed_rectangle({"at":[gx,gy,p.get("angle",0)],"layer":"F.Cu"},
                                                 [-halfx,-halfy,halfx,halfy])
                    inside = all(point_polygon_distance(q,outline) <= 0.001 for q in poly)
                    gap = min(*(polygon_boundary_distance(q,outline) for q in poly),
                              *(point_polygon_distance(q,poly) for q in outline))
                if not inside or gap < MIN_COPPER_EDGE_CLEARANCE_MM-0.001:
                    errors.append(f"{ref}:{number} copper violates actual outline/{MIN_COPPER_EDGE_CLEARANCE_MM:g}mm edge clearance")
    if outline is not None:
        for ref, fp in parts.items():
            if ref in PIN_SETS or not fp["pads"] or not all(p["kind"] == "np_thru_hole" for p in fp["pads"].values()):
                continue
            center = transform_points(fp, [(0,0)])[0]
            if point_polygon_distance(center,outline) > 0.001 or polygon_boundary_distance(center,outline) < 2.5-0.001:
                errors.append(f"5mm nylon support {ref} crosses actual native outline")
    return errors


def audit_courtyards(parts):
    polygons, errors = {}, []
    for ref, fp in parts.items():
        if not fp["courtyard_local_points"] or fp["dnp"]:
            continue
        polygons[ref] = courtyard_polygon(fp)
    for ref, a in polygons.items():
        for ref2, b in polygons.items():
            if ref >= ref2:
                continue
            if parts[ref]["layer"] != parts[ref2]["layer"]:
                continue
            if polygons_overlap(a, b):
                errors.append(f"Native assembly courtyards overlap: {ref}/{ref2}")
    return errors


def convex_hull(points):
    """Convex envelope of native courtyard vertices, conservatively filling gaps."""
    points = sorted(set(map(tuple, points)))
    def cross(o, a, b):
        return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    if len(points) < 3:
        raise ValueError("Degenerate courtyard polygon")
    lower, upper = [], []
    for target, seq in ((lower, points), (upper, reversed(points))):
        for p in seq:
            while len(target) >= 2 and cross(target[-2], target[-1], p) <= 0:
                target.pop()
            target.append(p)
    return lower[:-1] + upper[:-1]


def transform_points(fp, points):
    x, y, *angles = fp["at"]
    angle = math.radians(angles[0] if angles else 0)
    return [(x+px*math.cos(angle)+py*math.sin(angle),
             y-px*math.sin(angle)+py*math.cos(angle)) for px, py in points]


def courtyard_polygon(fp):
    return convex_hull(transform_points(fp, fp["courtyard_local_points"]))


def transformed_rectangle(fp, bounds, canonical=False):
    if canonical and fp["layer"] == "B.Cu":
        bounds = [bounds[0], -bounds[3], bounds[2], -bounds[1]]
    return transform_points(fp, [(bounds[0],bounds[1]),(bounds[2],bounds[1]),
                                 (bounds[2],bounds[3]),(bounds[0],bounds[3])])


def polygons_overlap(a, b, tolerance=0.001):
    """Strict convex-polygon overlap via normalized separating axes."""
    for polygon in (a, b):
        for p, q in zip(polygon, polygon[1:]+polygon[:1]):
            length = math.dist(p, q)
            if length < 1e-9:
                continue
            axis = (-(q[1]-p[1])/length, (q[0]-p[0])/length)
            pa = [x*axis[0]+y*axis[1] for x,y in a]
            pb = [x*axis[0]+y*axis[1] for x,y in b]
            if min(max(pa),max(pb)) <= max(min(pa),min(pb))+tolerance:
                return False
    return True


def point_polygon_distance(point, polygon):
    """Distance to a filled polygon; works for a concave board outline too."""
    x, y = point
    inside, distance = False, float("inf")
    for a,b in zip(polygon, polygon[1:]+polygon[:1]):
        dx,dy = b[0]-a[0],b[1]-a[1]
        denominator = dx*dx+dy*dy
        t = min(1,max(0,((x-a[0])*dx+(y-a[1])*dy)/denominator)) if denominator else 0
        distance = min(distance, math.hypot(x-a[0]-t*dx,y-a[1]-t*dy))
        if (a[1]>y) != (b[1]>y) and x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
            inside = not inside
    return 0.0 if inside else distance


def polygon_boundary_distance(point, polygon):
    distances = []
    for a,b in zip(polygon, polygon[1:]+polygon[:1]):
        dx,dy = b[0]-a[0],b[1]-a[1]
        denominator = dx*dx+dy*dy
        t = min(1,max(0,((point[0]-a[0])*dx+(point[1]-a[1])*dy)/denominator)) if denominator else 0
        distances.append(math.hypot(point[0]-a[0]-t*dx,point[1]-a[1]-t*dy))
    return min(distances)


def transformed_box(fp, bounds, canonical=False):
    # Native B.Cu primitives already have local Y negated by KiCad Flip.
    # Bounds from a manufacturer top-view drawing need that reflection here.
    if canonical and fp["layer"] == "B.Cu":
        bounds = [bounds[0], -bounds[3], bounds[2], -bounds[1]]
    x, y, *angles = fp["at"]
    angle = math.radians(angles[0] if angles else 0)
    points = [(x + px*math.cos(angle) + py*math.sin(angle),
               y - px*math.sin(angle) + py*math.cos(angle))
              for px in (bounds[0], bounds[2]) for py in (bounds[1], bounds[3])]
    return [min(p[0] for p in points), min(p[1] for p in points),
            max(p[0] for p in points), max(p[1] for p in points)]


def audit_fitted_envelopes(parts):
    """Independent conservative socket/housing allowances, not plug corridors.

    Bounds are in the corresponding manufacturer header-origin coordinates.
    Socket projections beyond PCB are rounded outward: Nano 2 mm, H2 1 mm,
    XIAO 3 mm. They are engineering allowances, not production tolerances.
    """
    errors, polygons, sides = [], {}, {}
    for ref, fp in parts.items():
        if fp["dnp"] or not fp["courtyard_local_points"]:
            continue
        polygons[ref] = courtyard_polygon(fp)
        sides[ref] = fp["layer"]
    for ref, bounds in USB_SHELL_BOUNDS.items():
        if ref not in parts:
            continue
        shell = transformed_rectangle(parts[ref], bounds, canonical=True)
        for other, polygon in polygons.items():
            if other != ref and sides[other] == parts[ref]["layer"] and polygons_overlap(shell, polygon):
                errors.append(f"Physical USB shell {ref} intersects fitted courtyard {other}")
        polygons[ref + "-USB"] = shell
        sides[ref + "-USB"] = parts[ref]["layer"]
    for ref in (f"J{i}" for i in range(1, 8)):
        if ref not in parts:
            continue
        n = len(parts[ref]["pads"])
        housing = transformed_rectangle(parts[ref], [-2.75, -1.75, 2.75, (n-1)*2.54+1.75], canonical=True)
        for other, polygon in polygons.items():
            if other not in (ref, ref + "-housing") and sides[other] == parts[ref]["layer"] and polygons_overlap(housing, polygon):
                errors.append(f"Fitted mating housing {ref} intersects {other}")
        polygons[ref + "-housing"] = housing
        sides[ref + "-housing"] = parts[ref]["layer"]
    for ref, fp in parts.items():
        if ref in PIN_SETS or not fp["pads"] or not all(p["kind"] == "np_thru_hole" for p in fp["pads"].values()):
            continue
        center = transform_points(fp, [(0,0)])[0]
        for other, polygon in polygons.items():
            if other != ref and point_polygon_distance(center, polygon) < 2.5-0.001:
                errors.append(f"5mm nylon support {ref} intersects {other}")
    return errors


def rectangle(bounds):
    x1,y1,x2,y2 = bounds
    return [(x1,y1),(x2,y1),(x2,y2),(x1,y2)]


def polygon_distance(a, b):
    """Filled simple-polygon separation, including crossing edges."""
    for p,q in zip(a,a[1:]+a[:1]):
        for r,s in zip(b,b[1:]+b[:1]):
            cross = lambda u,v,w: (v[0]-u[0])*(w[1]-u[1])-(v[1]-u[1])*(w[0]-u[0])
            if cross(p,q,r)*cross(p,q,s) < 0 and cross(r,s,p)*cross(r,s,q) < 0:
                return 0.0
    return min([point_polygon_distance(p,b) for p in a] +
               [point_polygon_distance(p,a) for p in b])


def native_pad_clearance(fp, pad, polygon):
    point = transform_points(fp,[pad["at"]])[0]
    if pad["shape"] == "circle":
        return point_polygon_distance(point,polygon)-max(pad["size"])/2
    sx,sy = pad["size"]
    # Bounding rectangle is conservative for oval and rounded-rectangle pads.
    copper = transformed_rectangle({"at":[*point,pad.get("angle",0)],"layer":"F.Cu"},
                                   [-sx/2,-sy/2,sx/2,sy/2])
    return polygon_distance(copper,polygon)


def audit_rail_contacts(parts, bounds, lands=None):
    """Nominal two-face rail fit with explicit solder-growth allowance.

    Plastic may overlap a courtyard margin, but never the source-derived body,
    a shell/housing, or the reserved solder envelope. This is not a Z/fit proof.
    """
    lands = RAIL_LANDS if lands is None else lands
    errors, result = [], {}
    if bounds != [0.0,0.0,47.5,75.0]:
        errors.append("Rail layout must have the selected 47.5 x 75 mm outline")
    supports = {r:p for r,p in parts.items() if r not in PIN_SETS}
    if set(supports) != {"H3"} or any(abs(a-b)>1e-5 for a,b in
            zip(supports.get("H3",{}).get("at",[])[:2], [18,52.03])):
        errors.append("Rail layout requires only H3 at (18,52.03)")
    h3_pads=list(supports.get("H3",{}).get("pads",{}).values())
    if (len(h3_pads)!=1 or h3_pads[0]["kind"]!="np_thru_hole" or
            abs(h3_pads[0]["drill"]-2.7)>1e-5):
        errors.append("H3 must retain the 2.7 mm non-plated retainer hole")
    obstacles = []
    for ref,fp in parts.items():
        if fp["dnp"] or ref not in PIN_SETS:
            continue
        poly = (transformed_rectangle(fp,MODULE_BODY_BOUNDS[ref],canonical=True)
                if ref in MODULE_BODY_BOUNDS else courtyard_polygon(fp))
        obstacles.append((ref,"body" if ref in MODULE_BODY_BOUNDS else "courtyard",poly))
        if ref in USB_SHELL_BOUNDS:
            obstacles.append((ref,"USB shell",transformed_rectangle(fp,USB_SHELL_BOUNDS[ref],canonical=True)))
        if ref in {f"J{i}" for i in range(1,8)}:
            n=len(fp["pads"])
            obstacles.append((ref,"mated housing",transformed_rectangle(fp,
                [-2.75,-1.75,2.75,(n-1)*2.54+1.75],canonical=True)))
    # The jack shell projects beyond the WIZ module PCB.
    obstacles.append(("U4","RJ45 shell",transformed_rectangle(parts["U4"],
        [2.11,-9.1,18.21,-6.4],canonical=True)))
    for name, box in lands.items():
        poly = rectangle(box)
        body_dist = sorted((polygon_distance(poly,p),r,kind) for r,kind,p in obstacles)
        pad_dist = sorted((native_pad_clearance(fp,pad,poly),r,pn)
            for r,fp in parts.items() for pn,pad in fp["pads"].items()
            if pad["kind"] == "thru_hole")
        support_dist = min((point_polygon_distance(fp["at"][:2],poly)-2.5
                            for fp in supports.values()),default=0)
        for distance,ref,kind in body_dist:
            if distance < RAIL_MARGIN_MM-1e-5:
                errors.append(f"{name} rail too close to {ref} {kind}: {distance:.4f} mm")
        for distance,ref,pn in pad_dist:
            if distance-SOLDER_FILLET_ALLOWANCE_MM < RAIL_MARGIN_MM-1e-5:
                errors.append(f"{name} rail insufficient solder margin at {ref}.{pn}: {distance:.4f} mm copper separation")
        if support_dist < RAIL_MARGIN_MM-1e-5:
            errors.append(f"{name} rail overlaps 5 mm H3 support clearance")
        result[name] = {"bounds_mm":box,"closest_body":body_dist[0][1:],
            "body_separation_mm":round(body_dist[0][0],6),
            "closest_pad":pad_dist[0][1:],"copper_separation_mm":round(pad_dist[0][0],6),
            "after_reserved_fillet_mm":round(pad_dist[0][0]-SOLDER_FILLET_ALLOWANCE_MM,6)}
    h2_ant = transformed_rectangle(parts["U2"],[4.83,-6.975,18.03,-1.575],canonical=True)
    h2_rail_distance = min(polygon_distance(h2_ant,rectangle(b)) for b in lands.values())
    if h2_rail_distance < 15-1e-5:
        errors.append("A rail enters the H2 antenna 15 mm housing-clearance recommendation")
    return errors,{"lands":result,"solder_growth_reserved_mm":SOLDER_FILLET_ALLOWANCE_MM,
        "minimum_residual_margin_mm":RAIL_MARGIN_MM,
        "h2_antenna_to_nearest_contact_land_mm":round(h2_rail_distance,6),
        "loading":"Open-loading split capture; no populated-board sliding groove",
        "z_fit_force_and_enclosure_rf_qualified":False,
        "limit":"Only contact lands audited. Full wall/lid geometry, actual fillets, underside heights, wire bends and load-bearing jack cradle still require measured checks."}


def audit_rail_copper(root, parts):
    """Check both-layer native keepouts and actual routed/fill geometry."""
    errors=[]
    for box in RAIL_COPPER_EXCLUSIONS:
        poly=rectangle(box)
        coverage=set()
        for zone in children(root,"zone"):
            keepout=one(zone,"keepout")
            if not keepout:
                continue
            points=[tuple(map(float,p[1:])) for p in one(["polygon",*one(zone,"polygon")],"pts")]
            # Corner containment alone must not bless a concave or self-crossed
            # keepout with an unprotected interior. Current rails use rectangles.
            bbox=[min(p[0] for p in points),min(p[1] for p in points),
                  max(p[0] for p in points),max(p[1] for p in points)]
            if len(points)!=4 or set(points)!=set(rectangle(bbox)) or polygons_overlap(
                    [points[0],points[1],points[2]], [points[0],points[2],points[3]]):
                continue
            if any(point_polygon_distance(p,points)>1e-5 for p in poly):
                continue
            if not all(one(["keepout",*keepout],k)==["not_allowed"] for k in ("tracks","vias","pads","copperpour")):
                continue
            coverage.update(one(zone,"layers") or one(zone,"layer") or [])
        if not {"F.Cu","B.Cu"}.issubset(coverage):
            errors.append(f"Missing full both-face copper exclusion for rail {box}")
        for ref,fp in parts.items():
            for pn,pad in fp["pads"].items():
                if pad["kind"] == "thru_hole" and native_pad_clearance(fp,pad,poly)<1e-5:
                    errors.append(f"Rail copper exclusion contains pad {ref}.{pn}")
        for item in children(root,"segment"):
            line=[tuple(map(float,one(item,k))) for k in ("start","end")]
            if polygon_distance(line,poly)<float(one(item,"width")[0])/2-1e-5:
                errors.append("Routed trace enters rail copper exclusion")
        for via in children(root,"via"):
            point=tuple(map(float,one(via,"at")))
            if point_polygon_distance(point,poly)<float(one(via,"size")[0])/2-1e-5:
                errors.append("Via enters rail copper exclusion")
        if children(root,"arc"):
            errors.append("Rail copper audit does not support native track arcs")
        for zone in children(root,"zone"):
            if one(zone,"keepout"):
                continue
            for filled in children(zone,"filled_polygon"):
                points=[tuple(map(float,p[1:])) for p in one(filled,"pts")]
                # KiCad may terminate a pour exactly on a keepout boundary.
                # Reject area inside it, not a shared zero-area boundary.
                interior=rectangle([box[0]+1e-5,box[1]+1e-5,box[2]-1e-5,box[3]-1e-5])
                if polygon_distance(points,interior)<1e-6:
                    errors.append("Filled copper enters rail exclusion")
    return errors


def endpoints(text):
    return [tuple(x.split(":", 1)) for x in text.split()]


# Signal labels are descriptive only: equality is checked by native net, not by
# comparing the generator's chosen net names. RX/TX below name the peripheral.
GROUPS = {k: endpoints(v) for k, v in {
    "input_5v": "J1:1 J2:1 J6:1 D1:2 D2:2 D3:2",
    "nano_vin": "D1:1 U1:JP1.15",
    "h2_5v": "D2:1 U2:J1.14",
    "xiao_vin": "D3:1 U3:14",
    "peripheral_3v3": "J2:3 J3:1 J4:1 J5:1 J7:2 U4:J2.2 U4:J2.3 R1:1 R2:1",
    "ground": "J1:2 J2:2 J2:4 J3:2 J4:2 J4:3 J5:2 J6:2 J7:1 J8:2 J9:2 U1:JP1.14 U1:JP2.4 U2:J1.13 U2:J1.15 U2:J3.1 U2:J3.10 U2:J3.12 U2:J3.15 U3:13 U4:J1.1 U4:J1.2 U4:J2.1",
    "spi_clock": "U1:JP1.10 U4:J1.4 J5:3",
    "spi_mosi": "U1:JP1.8 U4:J1.3 J5:4",
    "spi_miso": "U1:JP1.9 U4:J2.6 J5:5",
    "ethernet_cs": "U1:JP1.11 U4:J1.5",
    "ethernet_irq": "U1:JP2.10 U4:J1.6",
    "ethernet_reset": "U1:JP2.9 U4:J2.5",
    "rf_cs": "U1:JP2.6 J5:6 R2:2",
    "rf_tx_gdo0": "U1:JP1.7 J5:7 R1:2",
    "rf_rx_gdo2": "U1:JP2.5 J5:8",
    "thread_rx_gpio23": "U1:JP2.1 U2:J3.3",
    "thread_tx_gpio24": "U1:JP2.2 U2:J3.2",
    "thread_enable": "U1:JP2.15 U2:J1.2",
    "thread_boot_gpio9": "U1:JP1.1 U2:J3.11",
    "zigbee_rx_pc07": "U1:JP2.11 U3:8",
    "zigbee_tx_pc06": "U1:JP2.12 U3:7",
    "zigbee_cts_pc04": "U1:JP2.7 U3:5",
    "zigbee_rts_pc05": "U1:JP2.13 U3:6",
    "zigbee_boot_pc00": "J8:1 U3:1",
    "nano_boot_gpio0": "J9:1 U1:JP1.13",
    "i2c_sda": "U1:JP1.4 J3:3 J7:3",
    "i2c_scl": "U1:JP1.5 J3:4 J7:4",
    "radar_rx": "U1:JP2.8 J6:3",
    "radar_tx": "U1:JP2.14 J6:4",
    "zwave_rx": "J3:5 J4:4",
    "zwave_tx": "J3:6 J4:5",
}.items()}

PIN_SETS = {
    "U1": {f"{r}.{i}" for r in ("JP1", "JP2") for i in range(1, 16)},
    "U2": {f"{r}.{i}" for r in ("J1", "J3") for i in range(1, 16)},
    "U3": {str(i) for i in range(1, 15)},
    "U4": {f"{r}.{i}" for r in ("J1", "J2") for i in range(1, 7)},
    **{f"J{i}": {str(n) for n in range(1, count + 1)}
       for i, count in enumerate((2, 4, 6, 5, 8, 4, 4, 2, 2), 1)},
    **{ref: {"1", "2"} for ref in ("D1", "D2", "D3", "R1", "R2")},
}


def expected_xy(ref, number):
    if ref == "U1":
        row, n = number.split("."); n = int(n)
        return [0.0, (n - 1) * 2.54] if row == "JP1" else [15.24, (15 - n) * 2.54]
    if ref == "U2":
        row, n = number.split(".")
        return [0.0 if row == "J1" else 22.86, (int(n) - 1) * 2.54]
    if ref == "U3":
        n = int(number)
        return [0.0, (n - 1) * 2.54] if n <= 7 else [15.24, (14 - n) * 2.54]
    if ref == "U4":
        row, n = number.split(".")
        return [0.0 if row == "J1" else 20.32, (int(n) - 1) * 2.54]
    if ref.startswith("J"):
        return [0.0, (int(number) - 1) * 2.54]
    if ref.startswith(("D", "R")):
        return [(int(number) - 1) * 7.62, 0.0]
    return None


def assembly_access(parts):
    """Check explicit rear-first assembly, including shell/housing projections.

    A -> B means solder A before installing B. Any front -> rear dependency
    violates the required sequence even when the graph is acyclic. This is a
    plan-view access test; tails and underside parts still need measured Z.
    """
    fitted = {r: p for r, p in parts.items() if r in PIN_SETS and not p["dnp"]}
    bodies = {r: courtyard_polygon(p) for r,p in fitted.items() if p["courtyard_local_points"]}
    obstacles = [(r, "courtyard", poly) for r,poly in bodies.items()]
    for r, bounds in USB_SHELL_BOUNDS.items():
        if r in fitted:
            obstacles.append((r, "physical USB shell", transformed_rectangle(fitted[r], bounds, canonical=True)))
    for r in (f"J{i}" for i in range(1,8)):
        if r in fitted:
            n = len(fitted[r]["pads"])
            obstacles.append((r, "mating housing", transformed_rectangle(fitted[r],
                [-2.75,-1.75,2.75,(n-1)*2.54+1.75], canonical=True)))
    edges, overlaps, blockers, usb_projections = set(), [], [], []
    for ref, fp in fitted.items():
        for other, polygon in bodies.items():
            if (ref < other and fp["layer"] != fitted[other]["layer"] and ref in bodies
                    and polygons_overlap(bodies[ref], polygon)):
                overlaps.append([ref, other])
        for other, source, polygon in obstacles:
            if fp["layer"] == fitted[other]["layer"]:
                continue
            for pin, pad in fp["pads"].items():
                xy = transform_points(fp, [pad["at"]])[0]
                distance = point_polygon_distance(xy, polygon)
                if distance < SOLDER_ACCESS_RADIUS_MM:
                    edges.add((ref, other))
                    blockers.append({"solder_ref":ref,"pin":pin,"install_later":other,
                                     "obstacle":source,"clearance_mm":round(distance,4)})
                if source == "physical USB shell" and distance < max(pad["size"])/2:
                    usb_projections.append({"solder_ref":ref,"pin":pin,"shell_ref":other})
    remaining, order = set(fitted), []
    while remaining:
        ready = sorted((r for r in remaining if not any(b == r and a in remaining for a, b in edges)),
                       key=lambda r: (fitted[r]["layer"] != "B.Cu", r))
        if not ready:
            break
        order.extend(ready); remaining.difference_update(ready)
    errors = []
    if remaining:
        errors.append("Cyclic opposite-side solder access: " + ", ".join(sorted(remaining)))
    front_blockers = [b for b in blockers if fitted[b["solder_ref"]]["layer"] == "F.Cu"]
    if front_blockers:
        errors.append("Rear-first assembly hides front solder lands: " + ", ".join(sorted(
            {b["solder_ref"]+":"+b["pin"]+" under "+b["install_later"] for b in front_blockers})))
    fixed_order = sorted(r for r,p in fitted.items() if p["layer"] == "B.Cu") + sorted(
        r for r,p in fitted.items() if p["layer"] == "F.Cu")
    return errors, {"solder_access_radius_mm": SOLDER_ACCESS_RADIUS_MM,
                    "required_assembly_order": "All fitted rear parts, including WIZ, then all front controllers",
                    "solder_before_install_edges": [list(e) for e in sorted(edges)],
                    "candidate_solder_order": fixed_order,
                    "cycle_members": sorted(remaining),
                    "front_lands_blocked_by_fitted_rear_parts": front_blockers,
                    "usb_shell_solder_copper_projections_requiring_z_check": usb_projections,
                    "obstacles_checked": "Native courtyards, physical USB shells and fitted harness housings",
                    "opposite_side_body_overlaps_requiring_measured_z_clearance": overlaps,
                    "minimum_measured_conductor_clearance_mm": 1.0,
                    "z_qualified": False,
                    "limitation": "Rear-first access does not prove delivered tail length, module spacing, underside clearance or physical fit."}


def audit_rf_bodies(parts):
    # Geometric antenna reservations from manufacturer board geometry and the
    # reviewed edge allowance. These are not a claim of RF qualification.
    local = {"U1": [4, 33, 14, 39.37], "U2": [3, -6.975, 21, 10],
             "U3": [7, 13, 16, 18.034]}
    errors = []
    for owner, bounds in local.items():
        if owner not in parts:
            continue
        antenna = transformed_rectangle(parts[owner], bounds, canonical=True)
        for ref, fp in parts.items():
            if ref == owner or fp["dnp"] or not fp["courtyard_local_points"]:
                continue
            if polygons_overlap(antenna, courtyard_polygon(fp)):
                errors.append(f"{ref} body overlaps {owner} antenna reservation across board sides")
    return errors


def audit(parts):
    errors, assigned, nets = [], {}, {}
    for ref, expected in PIN_SETS.items():
        if ref not in parts:
            errors.append(f"Missing {ref}"); continue
        fp = parts[ref]
        if fp["dnp"] != (ref in {"J8", "J9"}):
            errors.append(f"{ref} fitted/DNP state differs from compact assembly contract")
        expected_layer = "B.Cu" if ref in REAR_REFS else "F.Cu"
        if fp["layer"] != expected_layer:
            errors.append(f"{ref} is not mounted on required side {expected_layer}")
        if set(fp["pads"]) != expected:
            errors.append(f"{ref} header pin set differs")
        for number, p in fp["pads"].items():
            if p["kind"] != "thru_hole":
                errors.append(f"{ref}:{number} is not a plated through-hole")
            if "*.Cu" not in p["layers"] and not {"F.Cu", "B.Cu"}.issubset(p["layers"]):
                errors.append(f"{ref}:{number} does not connect copper on both sides")
            xy = expected_xy(ref, number)
            if xy is not None and fp["layer"] == "B.Cu":
                xy = [xy[0], -xy[1]]
            if xy is not None and math.dist(xy, p["at"]) > 0.001:
                errors.append(f"{ref}:{number} manufacturer hole position differs")
            if ref.startswith("U") and xy is not None and (abs(p["drill"] - 1.1) > 0.001 or min(p["size"]) < 1.8):
                errors.append(f"{ref}:{number} module pin hole/pad allowance differs")
    for ref, fp in parts.items():
        if ref not in PIN_SETS and any(p["kind"] != "np_thru_hole" or p["net"] for p in fp["pads"].values()):
            errors.append(f"Unexpected electronic footprint {ref}")
    for group, members in GROUPS.items():
        group_nets = set()
        for ref, number in members:
            if (ref, number) in assigned:
                raise ValueError(f"Audit definition duplicates {ref}:{number}")
            assigned[(ref, number)] = group
            p = parts.get(ref, {}).get("pads", {}).get(number)
            if p is None:
                errors.append(f"Missing {ref}:{number} for {group}"); continue
            if not p["net"] or p["net"].startswith("unconnected-") or "no_connect" in p["type"]:
                errors.append(f"{ref}:{number} is unconnected but required for {group}")
            group_nets.add(p["net"])
        if len(group_nets) != 1:
            errors.append(f"{group} endpoints are split across nets")
        elif group_nets:
            net = next(iter(group_nets))
            if net in nets:
                errors.append(f"{group} is shorted to {nets[net]}")
            nets[net] = group
    all_net_counts = Counter(p["net"] for fp in parts.values() for p in fp["pads"].values() if p["net"])
    for ref in PIN_SETS:
        for number, p in parts.get(ref, {}).get("pads", {}).items():
            if (ref, number) not in assigned:
                if p["net"] and (not p["net"].startswith("unconnected-") or all_net_counts[p["net"]] != 1):
                    errors.append(f"Reserved {ref}:{number} is connected")
    return errors


def classify_drc(parts, drc):
    """Classify the exact documented 41 tail/body projections; suppress none."""
    malformed = (not isinstance(drc, dict) or
                 any(not isinstance(drc.get(k), list) for k in ("violations", "unconnected_items", "schematic_parity")))
    if not malformed:
        malformed = any(not isinstance(v, dict) or not isinstance(v.get("items"), list) or
                        not isinstance(v.get("type"), str) or not isinstance(v.get("severity"), str) or
                        any(not isinstance(i, dict) or not isinstance(i.get("uuid"), str) for i in v["items"])
                        for v in drc["violations"])
    if malformed:
        return ["Malformed native DRC report: required lists or item identifiers are missing"], {
            "native_findings": None, "classified_pth_body_projections": None,
            "unclassified_findings": None, "missing_expected_pairs": 41,
            "suppressed_in_kicad": 0, "mechanical_clearance_qualified": False,
            "validation_error": True}
    ids = {}
    for ref, fp in parts.items():
        ids[fp["uuid"]] = ("footprint", ref)
        for number, pad in fp["pads"].items():
            ids[pad["uuid"]] = ("pad", ref, number)
    expected = set()
    for ref in [*(f"J{i}" for i in range(1, 8)), "D1", "D3", "R1", "R2"]:
        owner = "U2" if ref.startswith("J") else ("U3" if ref == "D3" else "U1")
        for number in PIN_SETS[ref]:
            expected.add(frozenset({("pad", ref, number), ("footprint", owner)}))
    seen, errors = set(), []
    for item in drc["violations"]:
        pair = frozenset(ids.get(i["uuid"], ("unknown", i["uuid"])) for i in item["items"])
        if (item["type"] != "pth_inside_courtyard" or item["severity"] != "error" or
                pair not in expected or pair in seen):
            errors.append("Unclassified native DRC finding: " + item["type"] + " " + repr(sorted(pair)))
            continue
        pad_id = next(i for i in pair if i[0] == "pad")
        fp_id = next(i for i in pair if i[0] == "footprint")
        if parts[pad_id[1]]["layer"] != "B.Cu" or parts[fp_id[1]]["layer"] != "F.Cu":
            errors.append("Classified PTH projection no longer has expected rear/front sides")
        pad_fp, owner = parts[pad_id[1]], parts[fp_id[1]]
        xy = pad_fp["pads"][pad_id[2]]["at"]
        x, y, _, _ = transformed_box(pad_fp, [*xy, *xy])
        pts = owner["courtyard_local_points"]
        box = transformed_box(owner, [min(p[0] for p in pts), min(p[1] for p in pts),
                                      max(p[0] for p in pts), max(p[1] for p in pts)])
        if not (box[0] <= x <= box[2] and box[1] <= y <= box[3]):
            errors.append("Native DRC projection is stale relative to current footprint/pad positions")
        seen.add(pair)
    if seen != expected:
        errors.append(f"Expected exact 41 documented PTH/body projections, found {len(seen)}")
    return errors, {"native_findings": len(drc["violations"]), "classified_pth_body_projections": len(seen),
                    "unclassified_findings": len(drc["violations"])-len(seen),
                    "missing_expected_pairs": len(expected-seen), "suppressed_in_kicad": 0,
                    "mechanical_clearance_qualified": False,
                    "meaning": "Exact planned projections only; retained raw DRC errors require measured Z clearance before fabrication release."}


def evidence(cad):
    manifest = json.loads((cad / "verification.json").read_text())
    errors = []
    for name, expected in manifest["sha256"].items():
        actual = hashlib.sha256((cad / name).read_bytes()).hexdigest()
        if actual != expected:
            errors.append(f"Verification hash mismatch: {name}")
    checks = manifest["checks"]
    for key in ("erc_violations", "unconnected_items", "schematic_parity_issues"):
        if checks[key] != 0:
            errors.append(f"Native check {key}={checks[key]}")
    drc = json.loads((cad / "checks/drc.json").read_text())
    classification_errors, classification = classify_drc(read_board(cad / "mc1.kicad_pcb"), drc)
    errors.extend(classification_errors)
    if classification.get("validation_error"):
        report_hashes = {name: hashlib.sha256((cad / name).read_bytes()).hexdigest()
                         for name in ("checks/drc.json", "checks/erc.json")}
        return errors, len(manifest["sha256"]), checks, report_hashes, classification
    erc = json.loads((cad / "checks/erc.json").read_text())
    actual = {
        "erc_violations": sum(len(s["violations"]) for s in erc["sheets"]),
        "drc_violations": len(drc["violations"]),
        "unconnected_items": len(drc["unconnected_items"]),
        "schematic_parity_issues": len(drc["schematic_parity"]),
    }
    for key, value in actual.items():
        if value != checks[key]:
            errors.append(f"Native report/manifest mismatch: {key}")
    report_hashes = {name: hashlib.sha256((cad / name).read_bytes()).hexdigest()
                     for name in ("checks/drc.json", "checks/erc.json")}
    return errors, len(manifest["sha256"]), checks, report_hashes, classification


def mutations(parts, bounds):
    """Prove the independent audit catches plausible assembly/netlist mistakes."""
    def invade_usb(p):
        b = transformed_box(p["U1"], [2, -5.81, 13.24, -3.81], canonical=True)
        p["R2"].update(at=[(b[0]+b[2])/2, (b[1]+b[3])/2, 0.0], layer="F.Cu")
    def solder_cycle(p):
        x, y = p["U2"]["at"][:2]
        p["U4"].update(at=[x+1, y+25, 0.0])
    def invade_rf(p):
        b = transformed_box(p["U1"], [4, 33, 14, 39.37], canonical=True)
        p["J5"].update(at=[(b[0]+b[2])/2, (b[1]+b[3])/2, 0.0])
    cases = {
        "thread_tx_rx_swap": lambda p: swap_net(p, ("U2", "J3.3"), ("U2", "J3.2")),
        "zigbee_flow_control_swap": lambda p: swap_net(p, ("U3", "5"), ("U3", "6")),
        "shared_spi_split": lambda p: p["J5"]["pads"]["5"].update(net="/BROKEN_MISO"),
        "nano_vbus_connected": lambda p: p["U1"]["pads"]["JP1.12"].update(net=p["J1"]["pads"]["1"]["net"]),
        "regulator_outputs_joined": lambda p: p["U3"]["pads"]["12"].update(net=p["J2"]["pads"]["3"]["net"]),
        "supply_diode_short": lambda p: p["D1"]["pads"]["1"].update(net=p["D1"]["pads"]["2"]["net"]),
        "missing_manual_boot": lambda p: p.pop("J9"),
        "nano_reversed_row": lambda p: p["U1"]["pads"]["JP2.1"].update(at=[15.24, 0.0]),
        "passive_on_wrong_side": lambda p: p["R1"].update(layer="F.Cu"),
        "header_outside_board": lambda p: p["J5"].update(at=[-10.0, -10.0, 0.0]),
        "overlapping_diodes": lambda p: p["D2"].update(at=list(p["D1"]["at"])),
        "fitted_service_header": lambda p: p["J9"].update(dnp=False),
        "physical_usb_collision": invade_usb,
        "unmirrored_back_module_pad": lambda p: p["U4"]["pads"]["J1.2"].update(at=[0.0, 2.54]),
        "header_on_wrong_side": lambda p: p["J5"].update(layer="F.Cu"),
        "pth_missing_back_copper": lambda p: p["J5"]["pads"]["1"].update(layers=["F.Cu", "F.Mask"]),
        "cyclic_solder_order": solder_cycle,
        "back_header_under_antenna": invade_rf,
    }
    result = {}
    for name, change in cases.items():
        mutated = copy.deepcopy(parts)
        change(mutated)
        if name == "physical_usb_collision":
            result[name] = bool(audit_fitted_envelopes(mutated))
        elif name == "cyclic_solder_order":
            result[name] = bool(assembly_access(mutated)[0])
        elif name == "back_header_under_antenna":
            result[name] = bool(audit_rf_bodies(mutated))
        else:
            result[name] = bool(audit(mutated) + audit_pad_containment(mutated, bounds) + audit_courtyards(mutated) + audit_fitted_envelopes(mutated) + assembly_access(mutated)[0] + audit_rf_bodies(mutated))
    return result


def swap_net(parts, a, b):
    ap, bp = parts[a[0]]["pads"][a[1]], parts[b[0]]["pads"][b[1]]
    ap["net"], bp["net"] = bp["net"], ap["net"]


def geometry_regressions(parts):
    """Known geometry counterexamples; avoid AABB approval/rejection artifacts."""
    a = transformed_rectangle({"at":[0,0,45],"layer":"B.Cu"}, [0,-0.3,8,0.3])
    clear = transformed_rectangle({"at":[0,1,45],"layer":"B.Cu"}, [0,-0.3,8,0.3])
    hit = transformed_rectangle({"at":[0,0.2,45],"layer":"B.Cu"}, [0,-0.3,8,0.3])
    result = {"diagonal_parts_clear_despite_overlapping_bounds": not polygons_overlap(a, clear),
              "diagonal_parts_actual_collision_rejected": polygons_overlap(a, hit)}
    concave = [(0,0),(51,0),(51,48),(57,48),(57,75),(0,75)]
    bad = copy.deepcopy(parts)
    bad["J9"]["at"] = [54,20,0]
    result["pad_in_missing_flange_bbox_rejected"] = any("J9" in e for e in audit_pad_containment(bad,[0,0,57,75],concave))
    support = next(r for r in bad if r not in PIN_SETS)
    bad[support]["at"] = [54,49,0]
    result["support_crossing_flange_step_rejected"] = any(support in e for e in audit_pad_containment(bad,[0,0,57,75],concave))
    bad = copy.deepcopy(parts)
    bad["U3"]["at"] = [1.27,58.3,0]
    result["inside_pad_with_insufficient_edge_clearance_rejected"] = any(
        "U3" in e for e in audit_pad_containment(bad,[0,0,51,75],[(0,0),(51,0),(51,75),(0,75)]))

    # An acyclic graph may still require a front part before a rear part.
    bad = copy.deepcopy(parts)
    x,y = transform_points(bad["U3"], [bad["U3"]["pads"]["1"]["at"]])[0]
    rx,ry,*angles = bad["R2"]["at"]; angle = math.radians(angles[0] if angles else 0)
    bad["R2"]["courtyard_local_points"] = [
        [(gx-rx)*math.cos(angle)-(gy-ry)*math.sin(angle),
         (gx-rx)*math.sin(angle)+(gy-ry)*math.cos(angle)]
        for gx,gy in ((x-1,y-1),(x+1,y-1),(x+1,y+1),(x-1,y+1))]
    access_errors, access = assembly_access(bad)
    result["rear_first_rejects_acyclic_sequence"] = not access["cycle_members"] and any(
        "Rear-first" in e for e in access_errors)

    fixture = {r:copy.deepcopy(parts[r]) for r in ("U3","D2")}
    shell = transformed_rectangle(fixture["U3"],USB_SHELL_BOUNDS["U3"],canonical=True)
    point = (sum(q[0] for q in shell)/4, min(q[1] for q in shell)+0.1)
    fixture["D2"]["at"] = [*point,0]
    _,access = assembly_access(fixture)
    result["usb_shell_outside_courtyard_creates_dependency"] = (
        point_polygon_distance(point,courtyard_polygon(fixture["U3"])) > SOLDER_ACCESS_RADIUS_MM
        and ["D2","U3"] in access["solder_before_install_edges"])
    result["usb_shell_records_solder_projection_z_gate"] = bool(
        access["usb_shell_solder_copper_projections_requiring_z_check"])
    return result


def rail_regressions(parts, root, bounds):
    result={}
    bad=copy.deepcopy(parts); bad["U2"]["at"][0]-=0.2
    result["rail_front_body_or_fillet_clearance_rejected"]=bool(audit_rail_contacts(bad,bounds)[0])
    bad=copy.deepcopy(parts); bad["D2"]["at"]=[1.2,50.8,0]
    result["rail_rear_passive_rejected"]=bool(audit_rail_contacts(bad,bounds)[0])
    bad=copy.deepcopy(parts); bad["U3"]["at"]=[-3,58.3,0]
    result["rail_usb_projection_rejected"]=bool(audit_rail_contacts(bad,bounds)[0])
    bad=copy.deepcopy(parts); bad["H1"]=copy.deepcopy(bad["H3"])
    result["rail_extra_mount_rejected"]=bool(audit_rail_contacts(bad,bounds)[0])
    bad=copy.deepcopy(parts); bad.pop("H3")
    result["rail_missing_retainer_rejected"]=bool(audit_rail_contacts(bad,bounds)[0])
    bad=copy.deepcopy(RAIL_LANDS); bad["left"][2]=1.0
    result["rail_copper_only_approval_rejected_by_fillet"]=bool(audit_rail_contacts(parts,bounds,bad)[0])
    bad=copy.deepcopy(RAIL_LANDS); bad["left"][1]=12
    result["rail_h2_housing_margin_rejected"]=bool(audit_rail_contacts(parts,bounds,bad)[0])
    bad=[n for n in copy.deepcopy(root) if not (isinstance(n,list) and n and n[0]=="zone" and one(n,"keepout"))]
    result["rail_absent_native_exclusion_rejected"]=bool(audit_rail_copper(bad,parts))
    bad=copy.deepcopy(root)
    for zone in children(bad,"zone"):
        for field in children(zone,"keepout"):
            for flag in children(field,"vias"):
                flag[1]="allowed"
    result["rail_permissive_native_exclusion_rejected"]=bool(audit_rail_copper(bad,parts))
    bad=copy.deepcopy(root); bad.append(["segment",["start","-1","20"],["end","3","20"],["width","0.25"],["layer","B.Cu"]])
    result["rail_rear_crossing_trace_rejected"]=bool(audit_rail_copper(bad,parts))
    bad=copy.deepcopy(root); bad.append(["via",["at","0.8","20"],["size","0.6"],["layers","F.Cu","B.Cu"]])
    result["rail_via_high_spot_rejected"]=bool(audit_rail_copper(bad,parts))
    bad=copy.deepcopy(root); bad.append(["zone",["layer","F.Cu"],["filled_polygon",["layer","F.Cu"],["pts",["xy","0.2","20"],["xy","1","20"],["xy","1","21"],["xy","0.2","21"]]]])
    result["rail_ground_pour_rejected"]=bool(audit_rail_copper(bad,parts))
    touching=copy.deepcopy(root); touching.append(["zone",["layer","F.Cu"],["filled_polygon",["layer","F.Cu"],["pts",["xy","1.3","20"],["xy","1.5","20"],["xy","1.5","21"],["xy","1.3","21"]]]])
    result["rail_boundary_touch_without_interior_copper_allowed"]=not audit_rail_copper(touching,parts)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--board", type=Path, default=HERE / "cad/mc1.kicad_pcb")
    parser.add_argument("--skip-evidence", action="store_true", help="For a preliminary board before final exports")
    parser.add_argument("--self-test", action="store_true", help="Run mutation and geometry regressions in memory")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    parts = read_board(args.board)
    bounds = board_bounds(args.board)
    outline = board_outline(args.board)
    root = sexpr(args.board.read_text())
    access_errors, access = assembly_access(parts)
    rail_errors, rail_report = audit_rail_contacts(parts,bounds)
    errors = audit(parts) + audit_pad_containment(parts, bounds, outline) + audit_courtyards(parts) + audit_fitted_envelopes(parts) + access_errors + audit_rf_bodies(parts) + rail_errors + audit_rail_copper(root,parts)
    hashes, checks, report_hashes, classification = None, None, None, None
    if not args.skip_evidence:
        evidence_errors, hashes, checks, report_hashes, classification = evidence(args.board.parent)
        errors.extend(evidence_errors)
    mutation_results = mutations(parts, bounds) if args.self_test and not errors else {}
    if args.self_test and not errors:
        mutation_results.update(geometry_regressions(parts))
        mutation_results.update(rail_regressions(parts,root,bounds))
    if args.self_test and not errors and not args.skip_evidence:
        drc = json.loads((args.board.parent / "checks/drc.json").read_text())
        bad = copy.deepcopy(drc); bad["violations"][0]["type"] = "clearance"
        mutation_results["drc_other_type_not_excused"] = bool(classify_drc(parts, bad)[0])
        bad = copy.deepcopy(drc); bad["violations"].pop()
        mutation_results["drc_missing_expected_pair"] = bool(classify_drc(parts, bad)[0])
        bad = copy.deepcopy(drc); bad["violations"][0]["items"][1]["uuid"] = parts["U3"]["uuid"]
        mutation_results["drc_wrong_body_not_excused"] = bool(classify_drc(parts, bad)[0])
        for key in ("violations", "unconnected_items", "schematic_parity"):
            bad = copy.deepcopy(drc); bad.pop(key)
            mutation_results["drc_missing_list_" + key] = bool(classify_drc(parts, bad)[0])
        bad = copy.deepcopy(drc); bad["violations"].append(copy.deepcopy(bad["violations"][0]))
        mutation_results["drc_extra_violation_not_excused"] = bool(classify_drc(parts, bad)[0])
        bad_parts = copy.deepcopy(parts); bad_parts["U1"]["at"][0] += 100
        mutation_results["drc_stale_body_position"] = bool(classify_drc(bad_parts, drc)[0])
        bad_parts = copy.deepcopy(parts); bad_parts["D1"]["pads"]["1"]["at"][0] += 100
        mutation_results["drc_stale_pad_position"] = bool(classify_drc(bad_parts, drc)[0])
    errors.extend(f"Mutation not detected: {k}" for k, detected in mutation_results.items() if not detected)
    result = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "board": args.board.name,
        "board_sha256": hashlib.sha256(args.board.read_bytes()).hexdigest(),
        "audit_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "manufacturer_sources": SOURCES,
        "electronic_references": len(PIN_SETS),
        "fitted_electronic_references": sum(not parts[ref]["dnp"] for ref in PIN_SETS if ref in parts),
        "fitted_side_counts": dict(Counter(parts[ref]["layer"] for ref in PIN_SETS if ref in parts and not parts[ref]["dnp"])),
        "assembly_access": access,
        "rail_contact_review": rail_report,
        "expected_pads": sum(map(len, PIN_SETS.values())),
        "native_board_bounds_mm": bounds,
        "native_board_outline_mm": outline,
        "native_board_area_mm2": round(abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(outline,outline[1:]+outline[:1])))/2, 6),
        "native_support_centers_mm": {r: p["at"][:2] for r,p in parts.items() if r not in PIN_SETS},
        "connected_endpoint_groups": len(GROUPS),
        "connected_pads": sum(map(len, GROUPS.values())),
        "native_checks": checks,
        "native_report_sha256": report_hashes,
        "drc_classification": classification,
        "manifest_hashes_checked": hashes,
        "mutations_detected": mutation_results,
        "errors": errors,
        "passed": not errors,
        "fabrication_release": False,
        "limits": "Prototype consistency audit, not fabrication approval. Raw PTH/courtyard errors remain classified but unqualified pending measured Z clearance. No physical fit, power, RF, USB or runtime test.",
    }
    text = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(text)
    print(text, end="")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
