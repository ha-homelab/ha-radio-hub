// FIT COUPONS ONLY. Print on outer wall in the supplied orientation. Units mm.
// 1 / 2 / 3 edge notches correspond to 1.8 / 2.0 / 2.2 mm nominal gaps.
// Gap 1.8 mm; identification notches: 1
translate([0,0,0]) { translate([5.8, 0, 0]) { rotate([0, -90, 0]) { difference() {
union() {
cube([8.0,18.0,2.0]);
cube([3.0,18.0,5.8]);
translate([0, 0, 3.8]) { cube([4.2,18.0,2.0]); }
}
translate([7.0, 2, -0.02]) { cube([1.05,1.2,2.04]); }
} } } }
// Gap 2 mm; identification notches: 2
translate([10,0,0]) { translate([6.0, 0, 0]) { rotate([0, -90, 0]) { difference() {
union() {
cube([8.0,18.0,2.0]);
cube([3.0,18.0,6.0]);
translate([0, 0, 4.0]) { cube([4.2,18.0,2.0]); }
}
translate([7.0, 2, -0.02]) { cube([1.05,1.2,2.04]); }
translate([7.0, 5, -0.02]) { cube([1.05,1.2,2.04]); }
} } } }
// Gap 2.2 mm; identification notches: 3
translate([20,0,0]) { translate([6.2, 0, 0]) { rotate([0, -90, 0]) { difference() {
union() {
cube([8.0,18.0,2.0]);
cube([3.0,18.0,6.2]);
translate([0, 0, 4.2]) { cube([4.2,18.0,2.0]); }
}
translate([7.0, 2, -0.02]) { cube([1.05,1.2,2.04]); }
translate([7.0, 5, -0.02]) { cube([1.05,1.2,2.04]); }
translate([7.0, 8, -0.02]) { cube([1.05,1.2,2.04]); }
} } } }
