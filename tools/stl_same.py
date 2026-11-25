#!/usr/bin/env python3
"""Exit 0 if two STLs describe the same solid, 1 otherwise.

OpenSCAD re-exports of unchanged geometry can reorder triangles and even
re-triangulate flat faces differently. So "same" here means: the same set of
vertices and the same volume (within 0.01 mm³). Used by the Makefile to keep
the old file and avoid committing noise.

Usage: tools/stl_same.py old.stl new.stl
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_stl import read_stl  # noqa: E402


def signature(path):
    tris = read_stl(path)
    verts = {tuple(round(c, 5) for c in p) for t in tris for p in t}
    vol = 0.0
    for a, b, c in tris:
        vol += (a[0] * (b[1] * c[2] - b[2] * c[1])
                - a[1] * (b[0] * c[2] - b[2] * c[0])
                + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6.0
    return verts, vol


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    try:
        va, a = signature(sys.argv[1])
        vb, b = signature(sys.argv[2])
    except (OSError, ValueError):
        sys.exit(1)
    sys.exit(0 if va == vb and abs(a - b) < 0.01 else 1)


if __name__ == "__main__":
    main()
