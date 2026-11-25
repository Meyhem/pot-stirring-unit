// =====================================================================
//  Pot stirrer – angled bevel gearbox (30° default)
//  Input : 6 mm drive rod coming up from the motor, tilted shaft_angle from vertical
//  Output: 6 mm vertical shaft going straight down into the pot
//
//  Housing is split in two halves along the plane that contains both
//  shafts, so gears + bearings drop into one half and the other half
//  clamps them.  Halves are joined with M3 bolts through a flange.
//
//  Requires BOSL2  ->  https://github.com/BelfrySCAD/BOSL2
//  (clone it into your OpenSCAD libraries folder)
//
//  Hardware
//   - 4x 626 bearing (6x19x6), two per shaft – 626-2RS (sealed) for the lowest output one
//   - 6 mm steel rod: output shaft (stainless, into the food) + input stub
//   - 2x M3 grub screw + 2x M3 nut (gear set screws)
//   - 6x M3x12 bolt + nut (housing halves)
//   - 4x 4 mm countersunk wood screw, ~25 mm (housing -> wooden arm, 40x20)
//   - 2x 6 mm shaft collar (stop shafts sliding back out)
//   - flexible coupler (6 mm on the stub side) between motor/drill chuck and input stub
//
//  Printing: PETG / ASA / nylon, NOT PLA.  Housing halves split face down,
//  "supports on build plate only" (gear cavity roof + arm socket roof).
//  Gears flat back down, no supports, 4+ perimeters, 40%+ infill.
//
//  Assembly: grub screw nut into the slot on the gear back -> gear on rod
//  -> spacer (or M6 washers) -> bearings into half B -> close with half A -> bolts.
//  Rods may go up into the gear's hub boss, but must end >=1 mm below its top.
//  Each hub boss stops 0.3 mm short of a pad on the housing wall (axial stop).
//  Run the gears dry (no grease) – they sit above the food.
// =====================================================================

include <BOSL2/std.scad>
include <BOSL2/gears.scad>

/* [What to show / export] */
// assembly = preview; others are print-ready, laid flat
part = "assembly"; // [assembly, housing_a, housing_b, gear_out, gear_in, spacer, print_all]
// cut the housing in half in the assembly view
show_cutaway = true;

/* [Gears] */
shaft_angle = 30;     // angle between input and output shafts (input tilt from vertical)
gear_mod    = 2;      // module – 2 is a good size for PETG/ASA/nylon
pinion_teeth = 15;    // input gear (on motor rod)
gear_teeth   = 29;    // output gear (stirrer shaft)  -> ratio 29/15 ≈ 1.93:1
face_width   = 10;
gear_back    = 10;    // gear body thickness below pitch circle (holds the set screw)
backlash     = 0.2;   // extra play for printed teeth

/* [Shafts & bearings] */
shaft_d   = 6;        // steel rod
shaft_clr = 0.25;     // bore clearance in the gears
brg_od    = 19;       // 626 bearing (6x19x6)
brg_w     = 6;
brg_clr   = 0.3;      // pocket diameter clearance – tune to your printer
brg_hclr  = 0.4;      // pocket height clearance (6 mm bearing -> 6.4 mm pocket)
brg_gap   = 18;       // space between the two bearings on each shaft
brg_ledge = 1.75;     // shoulder that holds the outer race (must not touch inner race)
out_stub  = 0;        // extra tube length below lower output bearing

/* [Housing] */
wall       = 3;
gear_clear = 2.5;     // air gap around gear teeth
flange_w   = 9;       // how far the bolt flange sticks out
flange_t   = 5;       // flange thickness per half
bolt_d     = 3.4;     // M3 clearance
nut_w      = 5.7;     // M3 nut across flats (+clearance)
nut_h      = 2.6;

/* [Mounting: socket for a wooden arm parallel to the input rod] */
// The arm comes up from the motor board alongside the input rod (on the side
// away from the pot), slides into the socket and is fixed with wood screws
// driven sideways through the socket walls (2 per housing half).
mount       = true;
arm_w       = 40;     // arm width  (across, perpendicular to the shaft plane)
arm_t       = 20;     // arm thickness (towards/away from the input rod)
arm_clr     = 0.6;    // play around the wood
arm_gap     = 4;      // air between input bearing tube and the arm
socket_len  = 40;     // how deep the arm goes into the socket
socket_wall = 6;
screw_d     = 4.5;    // 4 mm wood screw clearance
screw_head_d = 8.5;   // countersink diameter

/* [Set screw (M3 grub screw + nut trap in each gear)] */
set_d = 3.2;

/* [Axial stop: hub boss on each gear + pad on the housing wall] */
// The boss rises from the gear face around the bore; a pad on the opposite
// housing wall stops just above it, so the gear cannot slide into the wall.
boss_d     = 12;      // hub boss diameter
pad_d      = 14;      // wall pad diameter
axial_gap  = 0.3;     // gap between boss top and wall pad

$fn = 64;

slices = 12;

// ---------------------------------------------------------------------
// Derived geometry
// ---------------------------------------------------------------------
rG = pitch_radius(mod=gear_mod, teeth=gear_teeth);
rP = pitch_radius(mod=gear_mod, teeth=pinion_teeth);
dG = bevel_pitch_angle(gear_teeth, pinion_teeth, shaft_angle=shaft_angle);
dP = bevel_pitch_angle(pinion_teeth, gear_teeth, shaft_angle=shaft_angle);

// Output gear: axis = +Z through origin, pitch base at z=0, shaft goes down.
// Input gear: axis tilted by shaft_angle around X, sits on +Y side.
u_in  = [0, -sin(shaft_angle), cos(shaft_angle)];      // input axis (towards apex)
c_in  = [0, rG + rP*cos(shaft_angle), rP*sin(shaft_angle)]; // input pitch base centre

tipG = rG + 1.2*gear_mod;   // a bit more than tip radius
tipP = rP + 1.2*gear_mod;
teeth_hG = face_width*cos(dG) + 1;   // tooth tip height above pitch base (+1 mm margin)
teeth_hP = face_width*cos(dP) + 1;

// bearing positions along each shaft, measured from the pitch base (negative = away from apex)
b1_top = -gear_back - 3;          // 3 mm = 1 mm air + 2 mm shoulder (spacer fills it)
b1_bot = b1_top - brg_w;
b2_top = b1_bot - brg_gap;
b2_bot = b2_top - brg_w;
tube_end = b2_bot - 2 - out_stub;
tube_r = brg_od/2 + wall + 1;

// Puts children into the input shaft frame (local Z = input axis, origin = pitch base)
module in_frame() {
    back(rG) xrot(shaft_angle) back(rP) children();
}

// ---------------------------------------------------------------------
// Gears
// ---------------------------------------------------------------------
module set_screw_cut(r_outer) {
    // radial M3 hole + nut trap open to the flat back face
    zs = -gear_back + 4;
    up(zs) xcyl(d=set_d, l=r_outer*2+2, anchor=LEFT, $fn=24);
    nut_r = shaft_d/2 + (r_outer - shaft_d/2)/2;
    translate([nut_r, 0, -gear_back - 0.01])
        cuboid([nut_h, nut_w, zs + gear_back + nut_w/2], anchor=BOT);
}

module gear_out() {
    difference() {
        bevel_gear(mod=gear_mod, teeth=gear_teeth, mate_teeth=pinion_teeth,
                   shaft_angle=shaft_angle, face_width=face_width,
                   bottom=gear_back, cone_backing=false, spiral=0,
                   backlash=backlash, shaft_diam=shaft_d+shaft_clr, slices=slices);
        set_screw_cut(rG - 2*gear_mod);
    }
    hub_boss(teeth_hG);
}

module gear_in() {
    difference() {
        bevel_gear(mod=gear_mod, teeth=pinion_teeth, mate_teeth=gear_teeth,
                   shaft_angle=shaft_angle, face_width=face_width,
                   bottom=gear_back, cone_backing=false, spiral=0, right_handed=true,
                   backlash=backlash, shaft_diam=shaft_d+shaft_clr, slices=slices);
        set_screw_cut(rP - 2*gear_mod);
    }
    hub_boss(teeth_hP);
}

// hub boss: tube from inside the gear body up to boss_top (gear frame, z=0 = pitch base)
module hub_boss(boss_top) {
    down(1) tube(od=boss_d, id=shaft_d + shaft_clr, h=boss_top + 1, anchor=BOT, $fn=48);
}

// spacer between gear back and inner race of the first bearing
module spacer() {
    tube(h=3 - 0.3, id=shaft_d+0.3, od=shaft_d+3.5, anchor=BOT, $fn=48);
}

// ---------------------------------------------------------------------
// Housing
// ---------------------------------------------------------------------
// cavity around one gear (in its own frame)
module gear_space(tip, th) {
    down(gear_back + 1) cyl(r=tip + gear_clear, h=gear_back + 1 + th + gear_clear, anchor=BOT);
}
module gear_body(tip, th) {
    down(gear_back + 1 + wall) cyl(r=tip + gear_clear + wall, h=gear_back + 1 + th + gear_clear + 2*wall, anchor=BOT);
}

module bearing_tube() {
    up(-gear_back - 1) cyl(r=tube_r, h=-tube_end - gear_back - 1, anchor=TOP);
}

module bearing_cuts() {
    // pockets
    up(b1_bot - brg_hclr/2) cyl(d=brg_od + brg_clr, h=brg_w + brg_hclr, anchor=BOT);
    up(b2_bot - brg_hclr/2) cyl(d=brg_od + brg_clr, h=brg_w + brg_hclr, anchor=BOT);
    // shaft clearance between/through (clears outer-race shoulder, not the inner race)
    up(tube_end - 1) cyl(d=brg_od - 2*brg_ledge, h=-tube_end + 1 + 1, anchor=BOT);
    // room between bearings so the shaft can be slid through
}

module shell_solid() {
    hull() {
        gear_body(tipG, teeth_hG);
        in_frame() gear_body(tipP, teeth_hP);
    }
    bearing_tube();
    in_frame() bearing_tube();
}

module cavity() {
    hull() {
        gear_space(tipG, teeth_hG);
        in_frame() gear_space(tipP, teeth_hP);
    }
}

// 2D outline of the housing in the YZ plane (split plane), mapped to XY
module profile2d() {
    projection() yrot(90) shell_solid();
}

// flange as a slab around the split plane
module flange() {
    difference() {
        yrot(-90)
            linear_extrude(height=2*flange_t, center=true, convexity=6)
                offset(r=flange_w) profile2d();
        // keep the flange from closing over the shaft exits:
        // trim it flush with the end of each bearing tube
        up(tube_end) cube([200, 200, 200], anchor=TOP);
        in_frame() up(tube_end) cube([200, 200, 200], anchor=TOP);
    }
}

side_dir = [0, cos(shaft_angle), sin(shaft_angle)];   // in-plane, away from the pot

// arm socket, in the input-shaft frame (local z = input axis, local +y = away from pot)
arm_y0   = tube_r + arm_gap;                 // arm face nearest to the rod
sock_top = -gear_back - 1 - wall;            // flush with the bottom of the gear body
sock_bot = sock_top - socket_len;
sock_W   = arm_w + arm_clr + 2*socket_wall;
sock_y0  = arm_y0 - arm_clr/2 - socket_wall;
sock_y1  = arm_y0 + arm_t + arm_clr/2 + socket_wall;
screw_z  = [sock_bot + 10, sock_top - 10];

module mount_solid() {
    if (mount) in_frame() {
        // socket box
        translate([0, sock_y0, sock_bot])
            cuboid([sock_W, sock_y1 - sock_y0, socket_len], anchor=FRONT+BOT, rounding=2, edges="Y");
        // web tying the socket to the bearing tube
        hull() {
            translate([0, 0, sock_bot]) cuboid([2*tube_r - 4, 1, socket_len], anchor=BOT);
            translate([0, sock_y0, sock_bot]) cuboid([2*tube_r - 4, 1, socket_len], anchor=BOT);
        }
    }
}
module mount_holes() {
    if (mount) in_frame() {
        // arm pocket, open towards the motor
        translate([0, arm_y0 - arm_clr/2, sock_bot - 1])
            cube([arm_w + arm_clr, arm_t + arm_clr, socket_len + 1 - socket_wall/2]
                 , anchor=FRONT+BOT);
        // wood screws through both side walls, countersunk on the outside
        for (sx = [-1, 1], z = screw_z)
            translate([sx*(arm_w/2 + arm_clr/2), arm_y0 + arm_t/2, z]) {
                xcyl(d=screw_d, l=2*socket_wall + 4, $fn=24);
                translate([sx*socket_wall, 0, 0])
                    yrot(sx > 0 ? 90 : -90) cyl(d1=screw_d, d2=screw_head_d + 0.5,
                         h=(screw_head_d - screw_d)/2 + 0.25, anchor=TOP, $fn=32);
            }
    }
}
module arm_ghost() {
    %in_frame() translate([0, arm_y0, sock_top - socket_wall/2 - 0.5])
        cuboid([arm_w, arm_t, 220], anchor=FRONT+TOP);
}

// bolt positions in YZ (y, z) – chosen around the profile, inside the flange
function bolt_pts() = let(
        e = tipG + gear_clear + wall + flange_w/2 + 0.5,
        in_dir = [0, sin(shaft_angle), -cos(shaft_angle)],   // pointing away from apex along input
        side   = [0, cos(shaft_angle),  sin(shaft_angle)],   // perpendicular to input, in plane
        rp     = tube_r + flange_w/2 + 0.5
    ) [
        [-e, -gear_back + 2],                      // left, low
        [-e,  teeth_hG],                            // left, high
        [-(tube_r + flange_w/2 + 0.5), tube_end + 8],  // output tube, left
        [ (tube_r + flange_w/2 + 0.5), tube_end + 8],  // output tube, right
        // along the input tube
        let(p = c_in + in_dir*(-tube_end - 8) - side*rp) [p.y, p.z],
        // top right over the pinion
        let(p = c_in + [0,-sin(shaft_angle),cos(shaft_angle)]*(teeth_hP) + side*(tipP + gear_clear + wall + flange_w/2)) [p.y, p.z],
    ];

module bolt_holes() {
    for (p = bolt_pts()) translate([0, p[0], p[1]]) {
        xcyl(d=bolt_d, l=200, $fn=24);
        // nut trap on side B, head recess on side A
        translate([-flange_t, 0, 0]) xcyl(d=nut_w/cos(30), l=10, $fn=6, anchor=RIGHT);
        translate([ flange_t, 0, 0]) xcyl(d=6.2, l=10, anchor=LEFT, $fn=24);
    }
}

// pads on the housing wall opposite each gear's hub boss
module wall_pads() {
    intersection() {
        hull() {   // inside of the outer gear shell only
            gear_body(tipG, teeth_hG);
            in_frame() gear_body(tipP, teeth_hP);
        }
        union() {
            up(teeth_hG + axial_gap) cyl(d=pad_d, h=60, anchor=BOT, $fn=48);
            in_frame() up(teeth_hP + axial_gap) cyl(d=pad_d, h=60, anchor=BOT, $fn=48);
        }
    }
}

module housing() {
  union() {
    difference() {
        union() {
            shell_solid();
            flange();
            mount_solid();
        }
        cavity();
        bearing_cuts();
        in_frame() bearing_cuts();
        bolt_holes();
        mount_holes();
    }
    wall_pads();
  }
}

module half(side) {   // side = +1 -> A (x>0), -1 -> B (x<0)
    intersection() {
        housing();
        translate([side*500, 0, 0]) cube(1000, center=true);
    }
}

// ---------------------------------------------------------------------
// Output
// ---------------------------------------------------------------------
module shafts() {
    color("silver") {
        down(gear_back) zcyl(d=shaft_d, h=130, anchor=TOP);
        in_frame() down(gear_back) zcyl(d=shaft_d, h=110, anchor=TOP);
    }
}

module bearings() {
    color("dimgray") for (f = [0, 1]) {
        multmatrix(f == 0 ? IDENT : (back(rG) * xrot(shaft_angle) * back(rP)))
            for (z = [b1_bot, b2_bot]) up(z) tube(h=brg_w, od=brg_od, id=shaft_d, anchor=BOT);
    }
}

if (part == "assembly") {
    color("orange") gear_out();
    color("lightblue") in_frame() gear_in();
    shafts();
    bearings();
    color("gray", 0.9) half(-1);
    if (!show_cutaway) color("gray", 0.5) half(1);
    if (mount) arm_ghost();
}
else if (part == "housing_a") yrot(-90) half(1);    // split face down
else if (part == "housing_b") yrot(90)  half(-1);   // split face down
else if (part == "gear_out")  up(gear_back) gear_out();
else if (part == "gear_in")   up(gear_back) gear_in();
else if (part == "spacer")    spacer();
else if (part == "print_all") {
    left(70)  yrot(-90) half(1);
    right(70) yrot(90)  half(-1);
    back(110) up(gear_back) gear_out();
    back(110) right(60) up(gear_back) gear_in();
    fwd(110) left(10) spacer();
    fwd(110) right(10) spacer();
}

echo(str("Ratio ", gear_teeth/pinion_teeth, ":1  | output pitch dia ", 2*rG, " mm, input pitch dia ", 2*rP, " mm"));
echo(str("Pitch angles: output ", dG, "°, input ", dP, "°"));
