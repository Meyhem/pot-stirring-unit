#!/usr/bin/env python3
"""Geometry fit checks: each check renders an intersection in OpenSCAD that
must come out EMPTY (gears don't hit each other or the housing, the motor,
drill head and arm don't hit the motor mount, ...).

The checks themselves are modules in the models (gb_check / mm_check); this
script runs them in parallel and reports PASS / FAIL.

Usage: tools/check_fit.py [name ...]      (no names = run all)
"""
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPENSCAD = os.environ.get("OPENSCAD", "openscad")

CHECKS = [
    # (name, model file, module call)
    ("gear_vs_gear",        "angled_gearbox.scad", 'gb_check("gear_vs_gear");'),
    ("housing_vs_gears",    "angled_gearbox.scad", 'gb_check("housing_vs_gears");'),
    ("axial_stop_out",      "angled_gearbox.scad", 'gb_check("axial_stop_out");'),
    ("axial_stop_in",       "angled_gearbox.scad", 'gb_check("axial_stop_in");'),
    ("mount_vs_motor",      "motor_mount.scad",    'mm_check("mount_vs_motor");'),
    ("mount_vs_drill_head", "motor_mount.scad",    'mm_check("mount_vs_drill_head");'),
    ("mount_vs_arm",        "motor_mount.scad",    'mm_check("mount_vs_arm");'),
    ("mount_vs_board",      "motor_mount.scad",    'mm_check("mount_vs_board");'),
    ("arm_vs_mount",        "arm.scad",            'arm_check("arm_vs_mount");'),
    ("arm_vs_gearbox",      "arm.scad",            'arm_check("arm_vs_gearbox");'),
    ("arm_halves",          "arm.scad",            'arm_check("arm_halves");'),
    ("pilots_vs_mount",     "arm.scad",            'arm_check("pilots_vs_mount");'),
    ("pilots_vs_gearbox",   "arm.scad",            'arm_check("pilots_vs_gearbox");'),
]


def run(check, tmp):
    name, model, call = check
    scad = os.path.join(tmp, name + ".scad")
    with open(scad, "w") as f:
        f.write(f"use <{os.path.join(ROOT, model)}>\n{call}\n")
    out = subprocess.run([OPENSCAD, "-o", os.path.join(tmp, name + ".stl"), scad],
                         capture_output=True, text=True)
    log = out.stdout + out.stderr
    bad = [l for l in log.splitlines() if "WARNING" in l or "ERROR" in l]
    # an unknown module/variable also renders "empty" – never let a warning pass
    if "Current top level object is empty" in log and not bad:
        return name, True, ""
    vol = [l.strip() for l in log.splitlines() if "Volumes" in l]
    return name, False, "; ".join(bad + vol) or "intersection is not empty"


def main():
    wanted = set(sys.argv[1:])
    checks = [c for c in CHECKS if not wanted or c[0] in wanted]
    if wanted - {c[0] for c in CHECKS}:
        sys.exit("unknown check(s): " + ", ".join(sorted(wanted - {c[0] for c in CHECKS})))
    with tempfile.TemporaryDirectory() as tmp, ThreadPoolExecutor(os.cpu_count() or 4) as ex:
        results = list(ex.map(lambda c: run(c, tmp), checks))
    failed = 0
    for name, ok, msg in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  – {msg}" if msg else ""))
        failed += not ok
    if failed:
        print(f"\n{failed} of {len(results)} fit check(s) failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
