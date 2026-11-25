#!/usr/bin/env bash
# Regenerate the README images in img/ from the .scad sources.
# Needs openscad + xvfb-run (headless) and BOSL2 in the OpenSCAD library path.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p img

LOG=$(mktemp)
trap 'rm -f "$LOG"' EXIT
# quiet render: print OpenSCAD's output only if it fails or warns
render() {
    local out
    out=$(printf '%s\n' "$@" | grep -m1 '\.png$')
    if ! xvfb-run -a openscad --imgsize=1200,900 --colorscheme=Tomorrow "$@" >"$LOG" 2>&1; then
        cat "$LOG"; echo "FAILED: $out"; exit 1
    fi
    grep -E "WARNING|ERROR" "$LOG" || true
    echo "render  $out"
}
R=(render)

# Gearbox
"${R[@]}" -o img/gearbox_cutaway.png --camera=0,35,-15,62,0,125,400 \
    -D 'part="assembly"' angled_gearbox.scad
"${R[@]}" -o img/gearbox_closed.png  --camera=0,35,-15,62,0,125,400 \
    -D 'part="assembly"' -D 'show_cutaway=false' angled_gearbox.scad
"${R[@]}" --render -o img/gearbox_print_parts.png --camera=0,0,0,30,0,0,620 \
    -D 'part="print_all"' angled_gearbox.scad

# Motor mount (one-piece: foot + arm cheeks + split motor ring)
"${R[@]}" -o img/motor_mount.png --camera=0,-50,100,90,0,90,650 \
    -D 'part="assembly"' motor_mount.scad
"${R[@]}" -o img/motor_mount_3d.png --camera=0,-40,70,60,0,230,450 \
    -D 'part="assembly"' motor_mount.scad
"${R[@]}" --render -o img/motor_mount_print_parts.png --camera=0,-20,50,120,0,40,420 \
    -D 'part="mount"' motor_mount.scad

echo "images updated in img/"
