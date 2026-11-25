# Stirrer – automatic pot stirrer (3D-printed)

DIY stirrer that stirs food in a pot on the stove. Nothing but the gearbox and
the stirring shaft sits above the food.

## The whole unit (top → bottom)
1. **Gearbox (top, above the pot)** – `angled_gearbox.scad`. Bevel gear pair in a
   split housing. Takes the tilted input rod and turns it into a vertical output shaft.
2. **Output shaft + paddle** – 6 mm stainless rod straight down into the pot, wooden
   paddle at the end (paddle not modelled yet).
3. **Input rod** – 6 mm steel rod running at 30° from vertical, from the motor up
   to the gearbox.
4. **Holding arm** – wooden 40×20 mm arm, parallel to the input rod, from the motor
   board up into a socket on the gearbox housing. It is the only thing holding the
   gearbox in the air. Not a printed part (plain wood), shown as a ghost in the assembly.
5. **Motor mount (bottom, beside the pot)** – `motor_mount_45.scad`. Cradle + 2 clamp
   caps for the TOPOWER 550-18V motor (RS-550, Ø38 mm body, 3.175 mm shaft), on a
   board next to the stove. A flexible coupler connects motor shaft → input rod.

## Files
- `angled_gearbox.scad` – parametric gearbox (current version: v4). Needs BOSL2.
- `motor_mount_45.scad` – motor cradle + clamps. Plain OpenSCAD, no libraries.
  Still at tilt=45, and its header/BOM still describes bolting to a 2020 aluminium
  profile with M5 T-nuts – outdated vs the wooden board/arm concept (see open items).
- `stl/` – exported gearbox parts at default parameters (housing_a/b, gear_in/out,
  spacer). Re-exported locally 2026-11-25 → byte-for-byte same geometry.
  No motor mount STLs here yet.
- `stirrer.3mf` – slicer project (2026-11-20) with gearbox + motor mount parts on
  2 plates. Older than the latest gearbox tweaks; re-slice from `stl/` before printing.
- `preview_cutaway.png`, `preview_gear_boss.png` – renders carried over from the chat.
- `prompt_regenerate_gearbox.md` – short spec (Slovak) to regenerate the gearbox from scratch.

## Local environment
- OpenSCAD 2021.01 at `/usr/bin/openscad` (old but works with current BOSL2).
- BOSL2 cloned to `~/.local/share/OpenSCAD/libraries/BOSL2` (update: `git -C … pull`).
- Headless PNG renders need `xvfb-run -a openscad …` (STL export works without it).
- Render times are short: housing ~5 s, gears ~4 s.
- Write scratch renders/STLs outside the project (or to a temp dir), only final
  exports go to `stl/`.
- Git repo, branch `main`, remote `origin` = git@github.com:Meyhem/pot-stirring-unit.git.
  STLs and the .3mf are tracked as deliverables; scratch `preview.png` is ignored.
- **Auto-push:** after every iteration (each finished change: geometry edit + checks,
  STL re-export, doc update) commit and `git push` to `origin main` without asking.

## Gearbox (angled_gearbox.scad) – current design
- Straight bevel pair (BOSL2 `bevel_gear`, spiral=0), shaft angle 30° (input tilted
  30° from vertical), module 2, 15T pinion / 29T output gear (~1.93:1), backlash 0.2.
  Pitch dia 58 / 30 mm, pitch angles 19.87° / 10.13°.
- 6 mm steel shafts, each in two 626 bearings (6×19×6), 18 mm apart.
  Pockets Ø19.3 × 6.4 mm (`brg_clr`, `brg_hclr`) – 6.0 mm pockets were too tight in a real print.
  Pocket ledge touches only the bearing outer race.
- Gears: flat back (cone_backing=false), M3 grub screw + M3 nut trap from the back,
  hub boss Ø12 on the front face. Housing has a Ø14 pad opposite each boss with
  `axial_gap` = 0.3 mm → gears cannot slide into the walls (real prints stalled without this).
  A spacer (or M6 washers) between gear back and upper bearing stops the other direction.
- Tooth tip height above pitch base = face_width·cos(pitch_angle) + 1 (NOT sin –
  that bug once left 0.15 mm wall clearance). Cavity = that + gear_clear (2.5).
- Housing split in two halves in the plane of both shafts (x=0), joined by 6 M3
  bolts through a flange; flange is trimmed flush with the bearing-tube ends so
  shaft exits stay open. Print halves split-face down, supports on build plate only.
- Mounting: socket on the outer side of the input tube (away from the pot) for the
  wooden arm 40×20 mm; 4 countersunk 4 mm wood screws through the socket side walls
  (2 per half). No mounting on top of the housing (unreachable).
- `part` selects output: assembly, housing_a, housing_b, gear_out, gear_in, spacer, print_all.
- Coordinate frame: output axis = +Z through origin (pitch base at z=0, shaft goes
  down), input gear on +Y side; `in_frame()` maps children into the input-shaft frame.

## Motor mount (motor_mount_45.scad) – current design
- Half-cylinder cradle tilted `tilt`° to the base plate, 2 half-ring clamp caps
  with M4 bolts, nuts slide into side slots; 1.5 mm squeeze gap.
- Rear clearance 12 mm for terminals; base plate with 2 adjustment slots.
- `part`: assembly, base, clamp, clamps_x2, print_all. Echo prints where the motor
  axis ends up relative to the plate (use it to align with the gearbox input).

## Rendering / checks (run after every geometry change)
```bash
# STL export (each part)
openscad -o stl/housing_a.stl -D 'part="housing_a"' angled_gearbox.scad
# preview image (headless)
xvfb-run -a openscad -o preview.png --imgsize=1400,1100 --camera=0,35,-15,62,0,125,400 -D 'part="assembly"' angled_gearbox.scad
```
Verification done so far with temporary `part` values (intersection must be EMPTY):
- gear vs gear: `intersection(){ gear_out(); in_frame() gear_in(); }`
- housing vs gears: `intersection(){ housing(); union(){ gear_out(); in_frame() gear_in(); } }`
- axial stop: shifting a gear 0.25 mm toward the wall → empty; 0.4 mm → contact only
  within the boss radius (never teeth).
Check exported STLs report `Simple: yes`. Look at the preview PNG after changes.

## Constraints / preferences
- Materials: PETG / ASA / nylon, never PLA (heat + steam). Gears run dry, no grease (above food).
- Nothing greasy or wet-sensitive directly above the pot; lowest output bearing 626-2RS.
- Keep everything parametric; keep the BOM + assembly notes at the top of each .scad in sync.

## Open items
- Motor mount: at 30° input the motor axis is 60° from a horizontal board → set
  `tilt = 60` in motor_mount_45.scad, OR mount the cradle directly on the wooden arm
  (arm becomes the spine: motor + gearbox auto-aligned). Not decided yet.
  Either way, update its header/BOM (still says 2020 profile + M5 T-nuts).
- Flexible coupler between motor shaft (3.175 mm on RS-550) and the 6 mm input rod
  (buy, or print a holder; motor_mount ghost assumes Ø19 × 25 mm).
- Paddle design (wooden, maybe scraping the bottom).
- No combined model of the full unit (gearbox + arm + motor mount) yet.
