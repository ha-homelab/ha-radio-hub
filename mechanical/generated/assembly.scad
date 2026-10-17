// Visualization only; print individual parts, not this assembly.
translate([0, 0, 0]) rotate([0, 0, 0]) import("base.stl");
translate([13.0, 13.0, 40.0]) rotate([0, 0, 0]) import("deck.stl");
translate([240.0, 0, 80.0]) rotate([0, 180, 0]) import("lid.stl");
translate([78.0, 14.0, 66.02]) rotate([0, 0, 0]) import("radar_carrier.stl");
translate([-75, 118.0, 40]) rotate([0, 0, 0]) import("bme680_pod_base.stl");
translate([-75, 118.0, 58.0]) rotate([0, 0, 0]) import("bme680_pod_lid.stl");
