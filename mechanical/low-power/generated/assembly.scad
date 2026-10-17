// Visualization only; not one printable object. Units mm.
// Opaque parts are printable; translucent boxes are allocation envelopes.
translate([0, 0, 0]) rotate([0, 0, 0]) import("mockup_base.stl");
translate([190.0, 0, 45.0]) rotate([0, 180, 0]) import("mockup_lid.stl");
translate([15.0, 12.0, 10.0]) rotate([0, 0, 0]) import("carrier_fit_blank.stl");
translate([60.0, 12.0, 33.6]) rotate([0, 0, 0]) import("radar_holder.stl");
color([0.2,0.65,0.7,0.45]) { translate([18.0, 24.0, 11.6]) { cube([32.0,28.0,12.0]); } } // S3
color([0.2,0.65,0.7,0.45]) { translate([142.0, 24.0, 11.6]) { cube([30.0,28.0,12.0]); } } // H2
color([0.2,0.65,0.7,0.45]) { translate([142.0, 64.0, 11.6]) { cube([32.0,29.0,12.0]); } } // MG24
color([0.2,0.65,0.7,0.45]) { translate([18.0, 65.0, 11.6]) { cube([42.0,35.0,14.0]); } } // ZAC93
color([0.2,0.65,0.7,0.45]) { translate([66.0, 38.0, 11.6]) { cube([32.0,24.0,12.0]); } } // CC1101
color([0.2,0.65,0.7,0.45]) { translate([107.0, 65.0, 11.6]) { cube([30.0,24.0,10.0]); } } // W5500
color([0.2,0.65,0.7,0.45]) { translate([105.0, 38.0, 11.6]) { cube([26.0,24.0,12.0]); } } // BUCK
color([0.2,0.65,0.7,0.45]) { translate([66.0, 67.0, 11.6]) { cube([32.0,22.0,14.0]); } } // UART
color([0.2,0.65,0.7,0.45]) { translate([66.0, 94.0, 11.6]) { cube([64.0,18.0,20.0]); } } // PD
color([0.2,0.65,0.7,0.45]) { translate([141.0, 96.0, 11.6]) { cube([33.0,21.0,20.0]); } } // RJ45
color([0.2,0.65,0.7,0.45]) { translate([73.0, 22.0, 35.6]) { cube([44.0,15.0,4.0]); } } // LD2450
color([0.2,0.65,0.7,0.45]) { translate([-65.0, 28.0, 12.0]) { cube([45.0,36.0,20.0]); } } // BME_POD_ENVELOPE
