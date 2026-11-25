// =====================================================================
//  Pot stirrer – parameters shared by angled_gearbox.scad and motor_mount.scad
//  Plain OpenSCAD (no libraries). Both files `include` this, so the gearbox,
//  the motor cradle and the arm foot always agree on the arm and the angle.
//
//  Frame used for everything on the arm ("arm frame"):
//    z = along the input rod / motor axis, pointing up towards the gearbox
//    y = perpendicular to the rod in the shaft plane, pointing from the rod
//        towards the arm (away from the pot, slightly upwards)
//    x = across (perpendicular to the shaft plane)
//    the rod / motor axis is the line x = y = 0
// =====================================================================

/* [Shared: geometry of the whole unit] */
// input rod tilt from vertical (= angle between input and output shafts);
// the arm and the motor are parallel to the rod, so they sit at
// 90 - shaft_angle to a horizontal board
shaft_angle = 30;

/* [Shared: drill chuck on the motor shaft] */
chuck_d   = 55;       // thickest part of the drill chuck
chuck_len = 90;       // body length incl. sleeve (only for the ghost – measure yours)
chuck_clr = 4;        // air between the spinning chuck and the arm

/* [Shared: wooden arm (20x40 on edge)] */
arm_w    = 20;        // across (x)
arm_t    = 40;        // in the shaft plane (y) = bending direction
arm_clr  = 0.6;       // play around the wood in printed cheeks
// distance from the rod axis to the arm's near face – set by the chuck
arm_y0   = chuck_d/2 + chuck_clr;

/* [Shared: cheeks + wood screws (gearbox, motor cradle, arm foot)] */
cheek_t      = 6;     // cheek thickness
screw_d      = 4.5;   // 4 mm wood screw clearance
screw_head_d = 8.5;   // countersink diameter
// screw positions per cheek as fractions [across arm_t, along the cheek];
// the cheek on -x uses the mirrored pattern, so screws from the two sides
// never meet inside the 20 mm wood
screw_pat    = [[0.25, 0.25], [0.75, 0.75]];

cheek_x = arm_w/2 + arm_clr/2;    // inner face of each cheek

// (y, z) of the screws in the cheek on side sx (+1 / -1), arm frame;
// y0 = arm near face, z0..z0+len = cheek extent along the arm
function arm_screw_yz(sx, y0, z0, len) = [for (p = screw_pat)
    [y0 + arm_t*(sx > 0 ? p[0] : 1 - p[0]), z0 + len*p[1]]];

// countersunk wood screw hole through the cheek on side sx, at (y, z)
module arm_screw_cut(sx, y, z) {
    translate([sx*cheek_x, y, z]) {
        rotate([0, 90, 0]) cylinder(d=screw_d, h=2*cheek_t + 2, center=true, $fn=24);
        hh = (screw_head_d - screw_d)/2 + 0.25;
        translate([sx*(cheek_t + 0.01), 0, 0]) rotate([0, sx > 0 ? -90 : 90, 0])
            cylinder(d1=screw_head_d + 0.5, d2=screw_d, h=hh, $fn=32);
    }
}
