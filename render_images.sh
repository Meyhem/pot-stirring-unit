#!/usr/bin/env bash
# Regenerate the README images in img/ from the .scad sources.
# Needs openscad + xvfb-run (headless) and BOSL2 in the OpenSCAD library path.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p img

R=(xvfb-run -a openscad --imgsize=1200,900 --colorscheme=Tomorrow)

# Gearbox
"${R[@]}" -o img/gearbox_cutaway.png --camera=0,35,-15,62,0,125,400 \
    -D 'part="assembly"' angled_gearbox.scad
"${R[@]}" -o img/gearbox_closed.png  --camera=0,35,-15,62,0,125,400 \
    -D 'part="assembly"' -D 'show_cutaway=false' angled_gearbox.scad
"${R[@]}" --render -o img/gearbox_print_parts.png --camera=0,0,0,30,0,0,620 \
    -D 'part="print_all"' angled_gearbox.scad

# Motor mount
"${R[@]}" -o img/motor_mount.png --autocenter --viewall --camera=0,0,0,65,0,210,0 \
    -D 'part="assembly"' motor_mount_45.scad
"${R[@]}" --render -o img/motor_mount_print_parts.png --autocenter --viewall --camera=0,0,0,45,0,30,0 \
    -D 'part="print_all"' motor_mount_45.scad

echo "images updated in img/"
