// CONCEPT MOCK-UP ONLY. Units mm. Generated from parameters.json; not a fabrication-ready PCB.
difference() {
union() {
cube([190.0,145.0,2.4]);
difference() {
translate([2.75, 2.75, 2.4]) { cube([184.5,139.5,2]); }
translate([4.35, 4.35, 2.38]) { cube([181.3,136.3,2.04]); }
translate([7.0, 7.0, 2.38]) { cylinder(d=11.0,h=2.04,$fn=48); }
translate([7.0, 138.0, 2.38]) { cylinder(d=11.0,h=2.04,$fn=48); }
translate([183.0, 7.0, 2.38]) { cylinder(d=11.0,h=2.04,$fn=48); }
translate([183.0, 138.0, 2.38]) { cylinder(d=11.0,h=2.04,$fn=48); }
}
translate([127.0, 15.0, 2.4]) { cylinder(d=8,h=7.0,$fn=48); }
translate([127.0, 47.0, 2.4]) { cylinder(d=8,h=7.0,$fn=48); }
translate([63.0, 15.0, 2.4]) { cylinder(d=8,h=7.0,$fn=48); }
translate([63.0, 47.0, 2.4]) { cylinder(d=8,h=7.0,$fn=48); }
}
translate([7.0, 7.0, -0.02]) { cylinder(d=3.4,h=2.44,$fn=48); }
translate([7.0, 138.0, -0.02]) { cylinder(d=3.4,h=2.44,$fn=48); }
translate([183.0, 7.0, -0.02]) { cylinder(d=3.4,h=2.44,$fn=48); }
translate([183.0, 138.0, -0.02]) { cylinder(d=3.4,h=2.44,$fn=48); }
translate([127.0, 15.0, 3.4000000000000004]) { cylinder(d=4.2,h=6.02,$fn=48); }
translate([127.0, 47.0, 3.4000000000000004]) { cylinder(d=4.2,h=6.02,$fn=48); }
translate([63.0, 15.0, 3.4000000000000004]) { cylinder(d=4.2,h=6.02,$fn=48); }
translate([63.0, 47.0, 3.4000000000000004]) { cylinder(d=4.2,h=6.02,$fn=48); }
translate([65.0, 16.0, 1.2]) { cube([60.0,30.0,1.22]); }
translate([38, 105.0, -0.02]) { cube([3,18,2.44]); }
translate([47, 105.0, -0.02]) { cube([3,18,2.44]); }
translate([56, 105.0, -0.02]) { cube([3,18,2.44]); }
translate([65, 105.0, -0.02]) { cube([3,18,2.44]); }
translate([74, 105.0, -0.02]) { cube([3,18,2.44]); }
translate([83, 105.0, -0.02]) { cube([3,18,2.44]); }
translate([92, 105.0, -0.02]) { cube([3,18,2.44]); }
translate([101, 105.0, -0.02]) { cube([3,18,2.44]); }
translate([110, 105.0, -0.02]) { cube([3,18,2.44]); }
translate([119, 105.0, -0.02]) { cube([3,18,2.44]); }
translate([128, 105.0, -0.02]) { cube([3,18,2.44]); }
translate([137, 105.0, -0.02]) { cube([3,18,2.44]); }
translate([146, 105.0, -0.02]) { cube([3,18,2.44]); }
}
