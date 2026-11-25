// =====================================================================
//  Pot stirrer – 45° motor mount (cradle + 2 clamp caps)
//  Motor: TOPOWER 550-18V (RS-550 class), body Ø38 mm (measured), ~57 mm long
//
//  The motor lies in a half-cylinder cradle tilted 45° to the base plate.
//  Two half-ring clamp caps bolt onto the cradle with M4 screws; nuts
//  slide in sideways into slots in the cradle (accessible from outside).
//  A small gap between cradle and clamp lets the bolts squeeze the motor.
//
//  Because the tilt is 45°, the same part works bolted to a HORIZONTAL
//  profile (motor points up at 45°) or a VERTICAL one (rotate it 90°).
//  Slots in the front tab let you slide it to line the motor shaft up
//  with the gearbox input stub (flexible coupler in between).
//
//  No libraries needed (plain OpenSCAD).
//
//  Hardware
//   - 4x M4x20 socket head screw + 4x M4 hex nut (clamps)
//   - 2x M5x10 screw + M5 T-nut (to the 2020 profile)
//   - optional: 1 mm rubber/TPU strip in the cradle for grip + damping
//
//  Printing: PETG/ASA. Base: plate down, no supports.
//  Clamps (part = "clamp"): lying on their ring face, no supports.
// =====================================================================

/* [What to show / export] */
part = "assembly"; // [assembly, base, clamp, clamps_x2, print_all]

/* [Motor] */
motor_d    = 38;     // measured body diameter
motor_len  = 57;     // body length without shaft (RS-550 ≈ 57)
motor_clr  = 0.3;    // diametral clearance in the bore
rear_clear = 12;     // space behind the motor for terminals + wires

/* [Cradle] */
tilt       = 45;     // motor axis angle to the base plate
cradle_len = 54;     // along the motor axis, from the rear face
floor_t    = 5;      // material under the motor
side_w     = 11.5;   // material beside the bore at the split line
squeeze_gap = 1.5;   // gap between cradle and clamp faces (clamping travel)
axis_lift  = 0;      // raise the whole motor further above the plate

/* [Clamps] */
clamp_w    = 12;     // width along the motor axis
clamp_t    = 5;      // ring thickness over the motor
ear_t      = 6;      // ear thickness under the bolt head
clamp_x    = [12, 42]; // clamp centres, measured from the motor rear face

/* [Bolts] */
bolt_d     = 4.4;    // M4 clearance
bolt_off   = 6;      // bolt axis distance outside the bore
bolt_depth = 16;     // how deep the bolt hole goes into the cradle
head_d     = 8;      // counterbore for M4 socket head
nut_w      = 7.2;    // M4 nut across flats + clearance
nut_h      = 3.4;
nut_depth  = 7;      // nut slot depth below the cradle face

/* [Base plate] */
base_t     = 6;
slot_d     = 5.5;    // M5
slot_len   = 10;     // adjustment travel per slot
slot_pitch = 17;     // distance between the two slots
ribbed     = true;   // ribs instead of a solid wedge (less plastic)
rib_t      = 5;

$fn = 96;
eps = 0.01;

// ---------------------------------------------------------------------
// Derived
// ---------------------------------------------------------------------
R  = (motor_d + motor_clr)/2;
hw = R + side_w;                 // half width of cradle / clamps
W  = 2*hw;
yb = R + bolt_off;               // bolt position (±Y)
s  = sin(tilt);
c  = cos(tilt);

// height of the motor axis at the rear face (x_M = 0), chosen so that
//  a) the cradle bottom clears the plate
//  b) the terminal space behind the motor clears the plate
z0 = base_t + axis_lift + max(
        (R + floor_t)*c,                       // cradle rear-bottom edge
        (rear_clear)*s + (R + 2)*c + 1         // terminal space
     );

// motor frame -> world  (x_M = motor axis, z_M = "up" out of the cradle)
module M() { translate([0, 0, z0]) rotate([0, -tilt, 0]) children(); }
function Mpt(p) = [p[0]*c - p[2]*s, p[1], z0 + p[0]*s + p[2]*c];

// footprint of the cradle bottom on the plate
Xr = Mpt([0,          0, -(R + floor_t)])[0];
Xf = Mpt([cradle_len, 0, -(R + floor_t)])[0];
plate_x0 = Xr - 3;
function slot_cx(i) = Xf + 4 + slot_d/2 + slot_len/2 + i*slot_pitch;
plate_x1 = slot_cx(1) + slot_len/2 + slot_d/2 + 5;

// 2D (Y,Z) profile -> extruded along x_M
module along_x(x0, len) {
    translate([x0, 0, 0]) rotate([90, 0, 90]) linear_extrude(len) children();
}

// ---------------------------------------------------------------------
// Cradle (motor frame)
// ---------------------------------------------------------------------
module cradle_2d() {
    difference() {
        translate([-hw, -(R + floor_t)]) square([W, R + floor_t - squeeze_gap/2]);
        circle(r = R);
        // chamfer the outer bottom corners a bit
        for (m = [0, 1]) mirror([m, 0])
            translate([hw, -(R + floor_t)]) rotate(45) square(4*sqrt(2), center = true);
    }
}

module cradle_bolt_cuts() {
    for (x = clamp_x, sy = [-1, 1]) translate([x, sy*yb, 0]) {
        // bolt hole
        translate([0, 0, -squeeze_gap/2 - bolt_depth]) cylinder(d = bolt_d, h = bolt_depth + 1, $fn = 24);
        // nut slot, open to the side
        translate([0, 0, -squeeze_gap/2 - nut_depth]) {
            rotate([0, 0, 30]) cylinder(d = nut_w/cos(30), h = nut_h, center = true, $fn = 6);
            translate([-nut_w/2, sy > 0 ? 0 : -(hw - yb + 2), -nut_h/2])
                cube([nut_w, hw - yb + 2, nut_h]);
        }
    }
}

module motor_cut() {
    // bore through the cradle and beyond both ends
    along_x(-rear_clear - 5, motor_len + rear_clear + 40) circle(r = R);
    // terminal / wire space behind the motor
    along_x(-rear_clear - 5, rear_clear + 5 + eps) circle(r = R + 2);
}

// ---------------------------------------------------------------------
// Support wedge + plate (world frame)
// ---------------------------------------------------------------------
// a thin slab along the cradle bottom, in motor frame
module bottom_slab(y0, wy) {
    M() translate([0, y0, -(R + floor_t)]) cube([cradle_len, wy, 1]);
}
module support_piece(y0, wy) {
    hull() {
        bottom_slab(y0, wy);
        translate([Xr, y0, 0]) cube([Xf - Xr, wy, base_t]);
    }
}
module support() {
    if (ribbed) {
        // two side walls + centre rib
        support_piece(-hw + 4, rib_t);          // inset to match the chamfers
        support_piece( hw - 4 - rib_t, rib_t);
        support_piece(-rib_t/2, rib_t);
        // closing wall at the front for stiffness
        hull() {
            M() translate([cradle_len - rib_t, -hw + 4, -(R + floor_t)]) cube([rib_t, W - 8, 1]);
            translate([Xf - rib_t*1.4, -hw + 4, 0]) cube([rib_t*1.4, W - 8, base_t]);
        }
    } else {
        support_piece(-hw + 4, W - 8);
    }
}

module plate() {
    difference() {
        translate([plate_x0, -hw + 4, 0])
            rounded_box([plate_x1 - plate_x0, W - 8, base_t], 4);
        // M5 slots along X in the front tab
        for (i = [0, 1])
            hull() for (dx = [-slot_len/2, slot_len/2])
                translate([slot_cx(i) + dx, 0, -1]) cylinder(d = slot_d, h = base_t + 2, $fn = 32);
    }
}

module rounded_box(size, r) {
    hull() for (x = [r, size[0] - r], y = [r, size[1] - r])
        translate([x, y, 0]) cylinder(r = r, h = size[2], $fn = 32);
}

module base() {
    difference() {
        union() {
            M() along_x(0, cradle_len) cradle_2d();
            difference() {
                support();
                // nothing of the support may rise above the cradle split face
                M() translate([-100, -100, -squeeze_gap/2]) cube([300, 200, 100]);
            }
            plate();
        }
        M() motor_cut();
        M() cradle_bolt_cuts();
    }
}

// ---------------------------------------------------------------------
// Clamp cap (2D in its own Y,Z plane, extruded clamp_w)
// ---------------------------------------------------------------------
module clamp_2d() {
    difference() {
        hull() {
            circle(r = R + clamp_t);
            translate([-hw, squeeze_gap/2]) square([W, ear_t]);
        }
        circle(r = R);
        translate([-100, -100]) square([200, 100 + squeeze_gap/2]);
    }
}

// clamp in "flat" coordinates: extruded along +Z (= print orientation)
module clamp_flat() {
    difference() {
        linear_extrude(clamp_w) clamp_2d();
        for (sy = [-1, 1]) translate([sy*yb, 0, clamp_w/2]) rotate([-90, 0, 0]) {
            translate([0, 0, -1]) cylinder(d = bolt_d, h = 100, $fn = 24);
            // counterbore from the ear top upward
            translate([0, 0, squeeze_gap/2 + ear_t]) cylinder(d = head_d, h = 100, $fn = 32);
        }
    }
}

// clamp placed in the motor frame, centred on x
module clamp_in_M(x) {
    translate([x - clamp_w/2, 0, 0]) rotate([90, 0, 90]) clamp_flat();
}

// ---------------------------------------------------------------------
// Ghosts for the assembly view
// ---------------------------------------------------------------------
module motor_ghost() {
    M() {
        color("dimgray") along_x(0, motor_len) circle(d = motor_d);
        color("silver") along_x(motor_len, 9) circle(d = 3.175, $fn = 24);
        color("goldenrod") along_x(-6, 6) square([10, 5], center = true);   // terminals
        color("orange", 0.8) along_x(motor_len + 4, 25) circle(d = 19);        // coupler
        color("silver") along_x(motor_len + 18, 40) circle(d = 6, $fn = 24);   // gearbox input stub
    }
}
module profile_ghost() {
    %translate([plate_x0 - 40, -10, -20]) cube([plate_x1 - plate_x0 + 80, 20, 20]);
}

// ---------------------------------------------------------------------
// Output
// ---------------------------------------------------------------------
if (part == "assembly") {
    color("lightsteelblue") base();
    for (x = clamp_x) color("tomato") M() clamp_in_M(x);
    motor_ghost();
    profile_ghost();
}
else if (part == "base")      base();
else if (part == "clamp")     clamp_flat();
else if (part == "clamps_x2") { clamp_flat(); translate([0, R + clamp_t + 10, 0]) clamp_flat(); }
else if (part == "print_all") {
    base();
    translate([plate_x1 + 15 + hw, 0, 0]) { clamp_flat(); translate([0, R + clamp_t + 10, 0]) clamp_flat(); }
}

// where the motor axis is, relative to the plate (bottom face = z 0, X along the plate)
front_axis = Mpt([motor_len, 0, 0]);
echo(str("Axis at rear face:  X=", Mpt([0,0,0])[0], "  Z=", z0));
echo(str("Axis at motor front face (shaft exit): X=", front_axis[0], "  Z=", front_axis[2]));
echo(str("Axis crosses the plate bottom plane at X=", -z0/tan(tilt)));
echo(str("Plate spans X=", plate_x0, " .. ", plate_x1, ", width ", W - 8));
