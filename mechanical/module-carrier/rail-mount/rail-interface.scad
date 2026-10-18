// SPLIT-RAIL INTERFACE STUDY, NOT A COMPLETE PRINTABLE ENCLOSURE.
// Coordinates match native PCB front view; local Z=0 is the lower ledge surface.
// Factory module heights, lid depth, jack stop and case attachments are UNKNOWN.
// Only the fit-coupon STL files are intended as printing trials.
board_width = 47.5;
board_height = 75.0;
// Inset from CAD maximum bands by the trial displacement budget.
// A measured case must bound movement of EVERY edge point, including rotation.
contact_bands = [[0, 15.2, 0.6499999999999999, 54.3], [46.5, 8.2, 47.5, 73.8]];
h3 = [18.0, 52.03];
pcb_preview_thickness = 1.6; // NOMINAL, not measured
slot_height = 2.0; // TRIAL ONLY: select after coupons
side_clearance = 0.2; // per edge, trial only
wall = 2.4;
lip = 2.4;
lid_lift = 8.0; // 0 for a closed interface preview
show_pcb = true;
mode = "exploded"; // "lower", "upper", "closed", "exploded"
assert(slot_height > pcb_preview_thickness);
module lower_rail(b, right=false) {
  x0 = right ? b[0] : -side_clearance-wall;
  x1 = right ? board_width+side_clearance+wall : b[2];
  wx = right ? board_width+side_clearance : -side_clearance-wall;
  union() {
    translate([x0,b[1],-lip]) cube([x1-x0,b[3]-b[1],lip]);
    translate([wx,b[1],-lip]) cube([wall,b[3]-b[1],lip+slot_height/2]);
  }
}
module upper_rail(b, right=false) {
  x0 = right ? b[0] : -side_clearance-wall;
  x1 = right ? board_width+side_clearance+wall : b[2];
  wx = right ? board_width+side_clearance : -side_clearance-wall;
  union() {
    translate([x0,b[1],slot_height]) cube([x1-x0,b[3]-b[1],lip]);
    translate([wx,b[1],slot_height/2]) cube([wall,b[3]-b[1],lip+slot_height/2]);
  }
}
module lower_interfaces() {for(i=[0:1]) lower_rail(contact_bands[i],i==1);}
module upper_interfaces() {for(i=[0:1]) upper_rail(contact_bands[i],i==1);}
// These separate rail volumes must be integrated into measured case halves.
// The renderer deliberately does not bridge antenna zones or invent screw bosses.
if(mode=="lower") color("Teal") lower_interfaces();
if(mode=="upper") color("SkyBlue") upper_interfaces();
if(mode=="closed" || mode=="exploded") {
  color("Teal") lower_interfaces();
  translate([0,0,mode=="exploded" ? lid_lift : 0]) color("SkyBlue") upper_interfaces();
  if(show_pcb) %difference() {
    cube([board_width,board_height,pcb_preview_thickness]);
    translate([h3[0],h3[1],-1]) cylinder(d=2.7,h=pcb_preview_thickness+2,$fn=48);
  }
}
