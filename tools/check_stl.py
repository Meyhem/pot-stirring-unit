#!/usr/bin/env python3
"""Check STL files for printability problems. Stdlib only.

For each file it checks:
  - parses (ASCII or binary STL), has triangles
  - no collapsed triangles (two corners at the same point); near-zero-area
    slivers from OpenSCAD's 6-digit output are only reported, slicers ignore them
  - watertight + manifold: every edge is shared by exactly 2 triangles
  - consistent winding: every directed edge appears exactly once
  - positive volume (normals point outwards)
  - number of separate bodies (shells) – more than 1 fails unless --allow-multi
  - fits the print bed (--bed X Y Z, default 220 220 250)

Exit code 0 = all files OK, 1 = at least one problem.

Usage: tools/check_stl.py [--bed 220 220 250] [--allow-multi] file.stl ...
"""
import argparse
import struct
import sys
from collections import Counter


def read_stl(path):
    """Return a list of triangles, each a tuple of 3 vertex tuples."""
    with open(path, "rb") as f:
        data = f.read()
    # binary STL: 80-byte header, uint32 count, 50 bytes per triangle
    if len(data) >= 84:
        n = struct.unpack_from("<I", data, 80)[0]
        if 84 + 50 * n == len(data):
            tris = []
            for i in range(n):
                v = struct.unpack_from("<12f", data, 84 + 50 * i)
                tris.append((v[3:6], v[6:9], v[9:12]))
            return tris
    # ASCII STL
    verts = []
    for line in data.decode("ascii", errors="replace").splitlines():
        parts = line.split()
        if parts and parts[0] == "vertex":
            verts.append(tuple(float(x) for x in parts[1:4]))
    if len(verts) % 3:
        raise ValueError("vertex count is not a multiple of 3")
    return [tuple(verts[i:i + 3]) for i in range(0, len(verts), 3)]


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def check(path, bed, allow_multi, sliver_area=1e-4):
    problems = []
    try:
        tris = read_stl(path)
    except Exception as e:  # noqa: BLE001
        return [f"cannot read: {e}"], {}
    if not tris:
        return ["no triangles"], {}

    # identical coordinates = same vertex (exporters write shared corners identically)
    index = {}
    def vid(p):
        key = (round(p[0], 6), round(p[1], 6), round(p[2], 6))
        return index.setdefault(key, len(index))

    faces = []
    collapsed = 0
    slivers = 0
    volume = 0.0
    for a, b, c in tris:
        n = cross(sub(b, a), sub(c, a))
        if (n[0] ** 2 + n[1] ** 2 + n[2] ** 2) ** 0.5 / 2 < sliver_area:
            slivers += 1
        ia, ib, ic = vid(a), vid(b), vid(c)
        if len({ia, ib, ic}) < 3:
            collapsed += 1
            continue
        faces.append((ia, ib, ic))
        volume += (a[0] * (b[1] * c[2] - b[2] * c[1])
                   - a[1] * (b[0] * c[2] - b[2] * c[0])
                   + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6.0
    if collapsed:
        problems.append(f"{collapsed} collapsed triangles (two corners at the same point)")

    undirected = Counter()
    directed = Counter()
    for f in faces:
        for i in range(3):
            u, v = f[i], f[(i + 1) % 3]
            directed[(u, v)] += 1
            undirected[(min(u, v), max(u, v))] += 1
    open_edges = sum(1 for c in undirected.values() if c == 1)
    nonmanifold = sum(1 for c in undirected.values() if c > 2)
    flipped = sum(1 for c in directed.values() if c > 1)
    if open_edges:
        problems.append(f"not watertight: {open_edges} open edges")
    if nonmanifold:
        problems.append(f"non-manifold: {nonmanifold} edges shared by >2 triangles")
    if flipped:
        problems.append(f"inconsistent winding: {flipped} edges with flipped triangles")
    if volume <= 0:
        problems.append(f"volume {volume:.1f} mm³ is not positive (normals point inwards?)")

    # shells = connected components over shared vertices (union-find)
    parent = list(range(len(index)))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b, c in faces:
        ra, rb, rc = find(a), find(b), find(c)
        parent[rb] = ra
        parent[find(rc)] = ra
    used = {v for f in faces for v in f}
    shells = len({find(v) for v in used})
    if shells > 1 and not allow_multi:
        problems.append(f"{shells} separate bodies (expected 1)")

    xs, ys, zs = zip(*(p for t in tris for p in t))
    size = (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    if any(s > b for s, b in zip(size, bed)):
        problems.append("does not fit the bed {}x{}x{}: size {:.1f} x {:.1f} x {:.1f}".format(*bed, *size))
    if min(zs) < -1e-3 or min(zs) > 1e-3:
        problems.append(f"lowest point is z={min(zs):.3f}, not on the bed (z=0)")

    stats = dict(triangles=len(tris), volume=volume, shells=shells, size=size, slivers=slivers)
    return problems, stats


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--bed", nargs=3, type=float, default=[220, 220, 250], metavar=("X", "Y", "Z"))
    ap.add_argument("--allow-multi", action="store_true", help="allow more than one body per file")
    args = ap.parse_args()

    bad = 0
    for path in args.files:
        problems, s = check(path, args.bed, args.allow_multi)
        if s:
            info = "{:>6} tris {:>7.1f} cm³  {:5.1f} x {:5.1f} x {:5.1f} mm".format(
                s["triangles"], s["volume"] / 1000, *s["size"])
            if s["slivers"]:
                info += f"  ({s['slivers']} harmless slivers)"
        else:
            info = ""
        if problems:
            bad += 1
            print(f"FAIL  {path}  {info}")
            for p in problems:
                print(f"        - {p}")
        else:
            print(f"ok    {path}  {info}")
    if bad:
        print(f"\n{bad} of {len(args.files)} file(s) have problems")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
