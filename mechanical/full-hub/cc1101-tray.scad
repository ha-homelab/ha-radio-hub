// Generated FH1 print part; mm. See parameters.json and physical-fit limits.
difference() {
union() {
cube([63,38,2.4]);
translate([0, 4, 0]) { cube([2,30,16]); }
translate([61, 4, 0]) { cube([2,30,16]); }
}
translate([2, 2, -0.1]) { cylinder(d=2.2,h=2.6,$fn=48); }
translate([61, 2, -0.1]) { cylinder(d=2.2,h=2.6,$fn=48); }
translate([2, 36, -0.1]) { cylinder(d=2.2,h=2.6,$fn=48); }
translate([61, 36, -0.1]) { cylinder(d=2.2,h=2.6,$fn=48); }
translate([18.9, 2.5, -0.1]) { cube([3,3,2.6]); }
translate([18.9, 32.5, -0.1]) { cube([3,3,2.6]); }
translate([44.099999999999994, 2.5, -0.1]) { cube([3,3,2.6]); }
translate([44.099999999999994, 32.5, -0.1]) { cube([3,3,2.6]); }
translate([-0.1, 6, 5.8]) { cube([4.2,26,20]); }
}
