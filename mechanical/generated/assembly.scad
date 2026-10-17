// Visualization only; print individual parts, not this assembly.
translate([0, 0, 0]) import("base.stl");
translate([13.0, 13.0, 40.0]) import("deck.stl");
translate([0, 0, 80.0]) mirror([0,0,1]) import("lid.stl");
translate([78.0, 14.0, 66.02]) import("radar_carrier.stl");
translate([255.0, 10, 0]) import("bme680_pod_base.stl");
translate([255.0, 10, 18.0]) import("bme680_pod_lid.stl");
