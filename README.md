# Pot stirring unit

A 3D-printed automatic stirrer for a pot on the stove. The motor sits **beside**
the pot, so nothing but a small gearbox and the stirring shaft is above the food.

![Gearbox cutaway](img/gearbox_cutaway.png)

## How it works

```
                 ┌──────────── gearbox (bevel gears, 2 bearings per shaft)
                 │      ╲  ╲
                 │       ╲  ╲  wooden arm 20×40 on edge = the spine
   output shaft  │        ╲  ╲
   (stainless)   │  input  ╲  ╲
                 │  rod 30° [chuck]
                 │           [motor]═╡ cradle screwed to the arm
        ┌────────┴────┐            ╲╲
        │   paddle    │           [foot]  ← holds the arm at 60°
        └─── pot ─────┘   ─────────────── board next to the stove
```

1. **Wooden arm:** 20×40 mm, standing on edge (the 40 mm side in the bending plane).
   It is the spine of the whole unit: a printed **foot** holds its bottom end on the
   board at 60°, and the motor cradle and the gearbox both grip it.
2. **Motor:** TOPOWER 550-18V (RS-550 class, Ø38 mm), in a printed cradle that hangs
   under the arm, on the same axis as the gearbox input.
3. **Drill head:** the motor drives a drill head: a planetary gearbox, a clutch collar
   (Ø55 mm, the thickest part) and a keyless chuck. The chuck grips the 6 mm steel
   input rod directly. The arm sits 31.5 mm from the rod axis, so the drill head
   clears it by 4 mm.
4. **Input rod:** goes up at 30° from vertical to the gearbox.
5. **Gearbox:** a straight bevel pair turns the tilted input into a vertical output
   (15T → 29T, about 1.93:1 reduction).
6. **Output shaft:** 6 mm stainless rod with a wooden paddle, straight down into the pot.

Because the motor and the gearbox are both positioned from the arm, they line up by
construction. The shared numbers (angle, arm size, chuck clearance, cheek and screw
pattern) live in `common.scad`.

## Gearbox – `angled_gearbox.scad`

| Closed housing | Print parts |
|---|---|
| ![closed](img/gearbox_closed.png) | ![print parts](img/gearbox_print_parts.png) |

- Module 2, 15T pinion / 29T gear, 30° shaft angle, 0.2 backlash (BOSL2 `bevel_gear`).
- Each 6 mm shaft runs in two 626 bearings (6×19×6), 18 mm apart.
- The housing is split in the plane of both shafts and the two halves are bolted
  together with 6× M3. Print each half split face down.
- Each gear has a hub boss that stops 0.3 mm short of a pad on the housing wall, so
  the gears can't slide into the wall:

  <img src="img/gear_boss.png" width="400" alt="gear hub boss">

- Arm mount: each housing half has one flat cheek that sits against a side of the
  arm, with 2 countersunk wood screws per cheek. The screws on the two sides are
  staggered so they don't meet inside the 20 mm wood. A cap on top is the end stop,
  so the arm end carries the gearbox weight, not the screws. The arm is not boxed in.

**Hardware:** 4× 626 bearing (the lowest output bearing must be 626-2RS),
6 mm stainless rod, 2× M3 grub screw + nut, 6× M3×12 bolt + nut,
4× 4 mm countersunk wood screw (~20 mm), 2× 6 mm shaft collar.

## Motor mount – `motor_mount.scad`

| Side view | The printed part |
|---|---|
| ![motor mount](img/motor_mount.png) | ![motor mount part](img/motor_mount_print_parts.png) |

<img src="img/motor_mount_3d.png" width="500" alt="motor mount 3D view">

**One printed part** (`part="mount"`, about 76 × 166 × 113 mm):
- **Plate:** screws to the board (4 wood screws). The arm's bottom end sits on it at 60°.
  Cut the arm's end 30° off square so it sits flat.
- **Cheeks:** one along each side of the arm, 4 wood screws per side (staggered).
- **Motor ring:** under the arm, on the gearbox input axis. It grips only the front
  39 mm of the can: the rear 18 mm (vent slots + end cap) stays open for cooling.
  A slit at the bottom is pinched shut by two M4 bolts.
- **Assembly:** push the motor into the ring from the front, rear end first, until
  the drill's beige gearbox housing sits against the ring's front face. That's also
  what stops the motor sliding backwards. Tighten the two pinch bolts. Set how deep the chuck grips the
  rod by sliding the rod in the chuck.
- **Clearance:** the motor terminals stay 10 mm above the board.

**Hardware:** 2× M4×20 socket head + 2× M4 nut, 8× 4 mm countersunk wood screw
(~20 mm, cheeks), 4× 4 mm countersunk wood screw (plate → board).

A three-part version (separate foot, a cradle that slides along the arm, and 2 clamp
caps) is still in the source as `style="three_piece"`. It has no ready-made STLs; export
them with `-D 'style="three_piece"' -D 'part="cradle"'` (or `clamp`, `foot`).

## Electronics – motor power control (`electronics/`)

The motor runs from a **19 V / 90 W laptop brick** (≈4.7 A). An Arduino Nano reads a
**speed pot** and drives a low-side MOSFET with 20 kHz PWM. A shunt resistor feeds an
analog pin, so the firmware can spot a jammed paddle. There is no op-amp or
comparator, just a few parts. The circuit is defined in code: `circuit.py` generates
ngspice netlists and holds all the parameters, `sim.py` simulates and checks them, and
`schematic.py` draws the schematic from the same values. The firmware isn't written yet.

![Schematic](img/circuit_schematic.png)

- **Power path:** brick → 5 A slow fuse → SMBJ22A TVS + 1000 µF bulk cap → motor → IRLZ44N
  (logic level, 100 Ω gate, 10 k pull-down) → **0.15 Ω / 5 W shunt** → ground. SB540
  Schottky flyback diode, 10 nF across the brushes (100 nF costs +0.2 W in the MOSFET at 20 kHz).
- **10 µF ceramic across the shunt:** a wire-wound (cement) shunt has ~1 µH of inductance.
  It sits in the MOSFET's source, so without the cap the source jumps ±5 V on every
  edge and the MOSFET loses 1.3 W. With the cap it's 0.34 W.
- **Current sense:** shunt → 10 kΩ / 47 nF → **A1**. A1 = 0.15 V/A of *supply*
  current (31 ADC counts/A). The motor current is A1 / duty, because the shunt only
  carries current while the MOSFET is on. The 10 kΩ keeps the pin's clamp current small
  when a full-speed jam drives the shunt to ~7 V.
- **Stall rule (firmware):** read A1 every 0.5 ms. If two samples in a row are over
  4.2 A supply current or over 8 A motor current, switch the PWM off.
- **Pot → A0. Logic power:** a buck module (MP1584 / LM2596) makes 5 V from the bus for
  the Nano's 5V pin.

What the simulation shows (`make circuit` → [`electronics/sim_results.md`](electronics/sim_results.md)):

| | |
|---|---|
| Start without a ramp (pot 0 → 60 %) | 36 A motor / 21 A supply peak, so the brick would shut down. **The firmware needs a soft-start.** |
| Soft-start ramp 0 → 99 % | 1 s peaks at 5.3 A (too much). **2.5 s → 4.0 A**, under the brick limit, no false stall |
| Full speed, normal load | ~18 900 rpm motor, 3.1 A, A1 = 95 counts, shunt 1.45 W |
| Paddle jams at 60 % / 30 % / 99 % | detected after 6.8 / 7.4 / 4.0 ms. The brick limit is reached at 7.5 / 17 / 4.2 ms, so detection always comes first. Without a PWM cut the motor would draw 35 A |
| 20 kHz switching at 60 % | MOSFET 0.34 W, diode 0.38 W, shunt 0.7 W, drain peak 21 V, A1 ripple 3.5 counts |

![Start-up](img/circuit_sim_startup.png)
![Stall](img/circuit_sim_stall.png)
![Switching](img/circuit_sim_switching.png)

Mount the shunt with an air gap above the board, away from the printed parts: it runs
at up to 3.3 W at the brick's limit. The motor model is an RS-550 estimate (0.23 Ω,
ke 0.0088 V·s/rad, 1.4 A no-load). The stirring load and jam torque are guesses.
**Measure the motor's resistance and no-load current, then update `P` in `circuit.py`.**

## Printing

| STL | Print | Supports |
|---|---|---|
| `housing_a.stl`, `housing_b.stl` | 1 each | build plate only (gear cavity roof, under the arm cheeks) |
| `gear_out.stl`, `gear_in.stl` | 1 each | none |
| `spacer.stl` | **2** (one per gear; the output gear needs it, the input one is optional) | none |
| `motor_mount_one_piece.stl` | 1 | build plate only (under the back of the motor ring) |

All STLs are already in print orientation.

- **PETG / ASA / nylon only.** Not PLA: it is too close to heat and steam.
- Housing halves: split face down, supports touching the build plate only.
- Gears: flat back down, no supports, 4+ perimeters, 40%+ infill.
- Motor mount (one piece): plate down, supports from the build plate only (under the
  back of the motor ring). If you're not sure how your printer sizes holes, print a
  short test ring first: tune `ring_clr` so the motor slides in easily.
- Three-piece variant: cradle standing on its rear end face, clamps on their ring
  face, foot plate down, no supports.
- Run the gears dry, with no grease, because they are above the food.
- All STLs are in [`stl/`](stl/). `stirrer.3mf` is an older slicer project; re-slice from `stl/`.

## Building from source

Requires [OpenSCAD](https://openscad.org) and [BOSL2](https://github.com/BelfrySCAD/BOSL2)
(for the gearbox), installed in your OpenSCAD libraries folder.

```bash
make            # build every printable STL into stl/ (only the ones whose source changed)
make check      # check all STLs + run the fit checks (see below)
make prune      # delete STLs in stl/ that are no longer current parts
make images     # re-render the README images (needs xvfb-run when headless)
make all-in     # all of the above
make rebuild    # force a re-export of every STL
make circuit    # simulate the motor power stage + draw its schematic
```

The electronics part needs `ngspice` (`apt install ngspice`). `make circuit` creates
`electronics/.venv` from `electronics/requirements.txt` the first time it runs. It
fails if any circuit check fails.

A single part by hand: `openscad -o x.stl -D 'part="housing_a"' angled_gearbox.scad`
(see `part` at the top of each .scad for the options).

### Checks

`make check` runs two tools (Python 3, no extra packages):

- **`tools/check_stl.py`** – checks each STL for printability: watertight and manifold
  (every edge shared by exactly 2 triangles), consistent winding, positive volume
  (normals pointing outwards), no collapsed triangles, one body per file, and that it
  fits the bed (`make check BED="220 220 250"`). It works on any STL:
  `tools/check_stl.py some.stl`.
- **`tools/check_fit.py`** – geometry checks in OpenSCAD; each one must come out
  empty: gear vs gear, housing vs gears, the axial stops (a gear pushed 0.25 mm towards
  the wall must not touch it), and motor mount vs motor, drill head, arm and board.

## Status / open items

- [x] Gearbox v4: includes fixes from earlier test prints (looser bearing pockets, axial stops)
- [x] Arm 20×40 on edge, gripped by cheeks (gearbox, motor cradle, foot)
- [x] Motor mount on the arm, with clearance for the drill chuck
- [x] One-piece motor mount (foot + cheeks + split motor ring)
- [ ] Print and test gearbox v4 and the motor mount (check the ring fit first)
- [ ] Measure the drill head (gearbox / collar / chuck lengths are estimated from a photo)
- [x] Motor power stage: circuit + ngspice simulation (start-up, stall, switching)
- [ ] Measure motor R / no-load current; build and test the power stage
- [ ] Arduino firmware: soft-start ramp, stall detection (A1), D2 trip, brick sag (A2)
- [ ] Wooden paddle
- [ ] Adjustable arm length (parked for now)
- [ ] Full-unit assembly model (gearbox + arm + motor mount)
