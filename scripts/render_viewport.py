"""Render the hero viewport: a tiny Cornell-box path tracer.

Writes progressive frames (1 / 4 / 16 / 64 / 256 spp) to assets/src/viewport-<spp>.jpg.
The hero SVG cross-fades them so the image "converges" like a real progressive render.

    pip install numpy pillow
    python scripts/render_viewport.py
"""

import os
from pathlib import Path

import numpy as np
from PIL import Image

W, H = 400, 360
MAX_DEPTH = 6
CHECKPOINTS = tuple(int(x) for x in os.environ.get("SPP", "1,4,16,64,256").split(","))
OUT = Path(__file__).resolve().parent.parent / "assets" / "src"

rng = np.random.default_rng(20261006)

# --- scene ----------------------------------------------------------------
# Box spans [-1, 1]^3, camera looks down -z through the open front.
# Walls: (axis, value, inward normal sign, albedo)
WHITE = (0.74, 0.73, 0.70)
WALLS = [
    (0, -1.0, +1, (0.86, 0.66, 0.04)),  # left   - hazard yellow
    (0, +1.0, -1, (0.07, 0.56, 0.66)),  # right  - terminal cyan
    (1, -1.0, +1, WHITE),  # floor
    (1, +1.0, -1, WHITE),  # ceiling (holds the light)
    (2, -1.0, +1, WHITE),  # back
]
LIGHT_HALF = 0.32
LIGHT_Y = 0.999
LIGHT_EMIT = np.array([17.0, 15.6, 13.4])
LIGHT_AREA = (2 * LIGHT_HALF) ** 2

# Spheres: center, radius, kind (0 diffuse, 1 mirror, 2 glass), albedo
SPHERES = [
    ((-0.45, -0.62, -0.38), 0.38, 1, (0.95, 0.95, 0.95)),
    ((0.46, -0.64, 0.22), 0.36, 2, (1.0, 1.0, 1.0)),
    ((0.02, -0.88, 0.52), 0.12, 0, (1.0, 0.42, 0.10)),  # small orange marker
]
IOR = 1.5

CAM = np.array([0.0, 0.0, 3.95])
FOV = np.deg2rad(39.0)


def normalize(v):
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def intersect(o, d):
    """Return t, normal, albedo, kind, emissive mask for each ray."""
    n = o.shape[0]
    t = np.full(n, np.inf)
    nrm = np.zeros((n, 3))
    alb = np.zeros((n, 3))
    kind = np.full(n, -1)
    emit = np.zeros(n, bool)

    for axis, val, sign, albedo in WALLS:
        dd = d[:, axis]
        with np.errstate(divide="ignore", invalid="ignore"):
            tt = (val - o[:, axis]) / dd
        hit = (tt > 1e-4) & (tt < t)
        p = o + d * np.where(np.isfinite(tt), tt, 0)[:, None]
        others = [a for a in range(3) if a != axis]
        hit &= np.all(np.abs(p[:, others]) <= 1.0001, axis=1)
        t = np.where(hit, tt, t)
        nv = np.zeros(3)
        nv[axis] = sign
        nrm[hit] = nv
        alb[hit] = albedo
        kind[hit] = 0
        if axis == 1 and val > 0:
            lit = hit & (np.abs(p[:, 0]) < LIGHT_HALF) & (np.abs(p[:, 2]) < LIGHT_HALF)
            emit = np.where(hit, lit, emit)
        else:
            emit = np.where(hit, False, emit)

    for c, r, k, albedo in SPHERES:
        c = np.array(c)
        oc = o - c
        b = np.einsum("ij,ij->i", oc, d)
        cc = np.einsum("ij,ij->i", oc, oc) - r * r
        disc = b * b - cc
        ok = disc > 0
        sq = np.sqrt(np.where(ok, disc, 0))
        t0 = -b - sq
        t1 = -b + sq
        tt = np.where(t0 > 1e-4, t0, t1)
        hit = ok & (tt > 1e-4) & (tt < t)
        t = np.where(hit, tt, t)
        p = o + d * np.where(hit, tt, 0)[:, None]
        nrm[hit] = ((p - c) / r)[hit]
        alb[hit] = albedo
        kind[hit] = k
        emit = np.where(hit, False, emit)

    return t, nrm, alb, kind, emit


def shadow(o, d, dist):
    """Only the spheres can occlude the light: the box itself is convex."""
    blocked = np.zeros(o.shape[0], bool)
    for c, r, _, _ in SPHERES:
        oc = o - np.array(c)
        b = np.einsum("ij,ij->i", oc, d)
        disc = b * b - (np.einsum("ij,ij->i", oc, oc) - r * r)
        ok = disc > 0
        sq = np.sqrt(np.where(ok, disc, 0))
        tt = np.where(-b - sq > 1e-4, -b - sq, -b + sq)
        blocked |= ok & (tt > 1e-4) & (tt < dist - 1e-4)
    return blocked


def cosine_hemisphere(nrm):
    n = nrm.shape[0]
    u1, u2 = rng.random(n), rng.random(n)
    r = np.sqrt(u1)
    phi = 2 * np.pi * u2
    local = np.stack([r * np.cos(phi), r * np.sin(phi), np.sqrt(1 - u1)], axis=1)
    a = np.where(np.abs(nrm[:, :1]) > 0.9, [[0.0, 1.0, 0.0]], [[1.0, 0.0, 0.0]])
    tng = normalize(np.cross(a, nrm))
    btg = np.cross(nrm, tng)
    return normalize(local[:, :1] * tng + local[:, 1:2] * btg + local[:, 2:] * nrm)


def camera_rays():
    ys, xs = np.mgrid[0:H, 0:W]
    xs = xs.ravel() + rng.random(W * H)
    ys = ys.ravel() + rng.random(W * H)
    aspect = W / H
    scale = np.tan(FOV / 2)
    px = (2 * xs / W - 1) * aspect * scale
    py = (1 - 2 * ys / H) * scale
    d = normalize(np.stack([px, py, -np.ones_like(px)], axis=1))
    o = np.broadcast_to(CAM, d.shape).copy()
    return o, d


def trace_pass():
    o, d = camera_rays()
    n = o.shape[0]
    radiance = np.zeros((n, 3))
    throughput = np.ones((n, 3))
    alive = np.ones(n, bool)
    count_emit = np.ones(n, bool)  # camera ray or last bounce specular

    for _ in range(MAX_DEPTH):
        idx = np.nonzero(alive)[0]
        if idx.size == 0:
            break
        t, nrm, alb, kind, emit = intersect(o[idx], d[idx])
        miss = ~np.isfinite(t)
        alive[idx[miss]] = False

        hit_light = emit & count_emit[idx] & ~miss
        radiance[idx[hit_light]] += throughput[idx[hit_light]] * LIGHT_EMIT
        stop = emit & ~miss
        alive[idx[stop]] = False

        keep = ~miss & ~emit
        idx, t, nrm, alb, kind = idx[keep], t[keep], nrm[keep], alb[keep], kind[keep]
        if idx.size == 0:
            break
        dd = d[idx]
        p = o[idx] + dd * t[:, None]
        front = np.einsum("ij,ij->i", nrm, dd) < 0
        ffn = np.where(front[:, None], nrm, -nrm)

        # diffuse: next-event estimation + cosine bounce
        dif = kind == 0
        if dif.any():
            di = idx[dif]
            pd = p[dif]
            nd = ffn[dif]
            m = di.size
            lp = np.stack(
                [
                    (rng.random(m) * 2 - 1) * LIGHT_HALF,
                    np.full(m, LIGHT_Y),
                    (rng.random(m) * 2 - 1) * LIGHT_HALF,
                ],
                axis=1,
            )
            to_l = lp - pd
            dist2 = np.einsum("ij,ij->i", to_l, to_l)
            dist = np.sqrt(dist2)
            ldir = to_l / dist[:, None]
            cos_s = np.clip(np.einsum("ij,ij->i", nd, ldir), 0, None)
            cos_l = np.clip(ldir[:, 1], 0, None)
            vis = ~shadow(pd + nd * 1e-4, ldir, dist)
            g = cos_s * cos_l / dist2 * LIGHT_AREA / np.pi
            radiance[di] += (
                throughput[di] * alb[dif] * LIGHT_EMIT * (g * vis)[:, None]
            )
            throughput[di] *= alb[dif]
            o[di] = pd + nd * 1e-4
            d[di] = cosine_hemisphere(nd)
            count_emit[di] = False

        mir = kind == 1
        if mir.any():
            mi = idx[mir]
            nm = ffn[mir]
            dm = dd[mir]
            r = dm - 2 * np.einsum("ij,ij->i", dm, nm)[:, None] * nm
            throughput[mi] *= alb[mir]
            o[mi] = p[mir] + nm * 1e-4
            d[mi] = normalize(r)
            count_emit[mi] = True

        gls = kind == 2
        if gls.any():
            gi = idx[gls]
            ng = ffn[gls]
            dg = dd[gls]
            fr = front[gls]
            eta = np.where(fr, 1 / IOR, IOR)
            cosi = -np.einsum("ij,ij->i", dg, ng)
            k = 1 - eta**2 * (1 - cosi**2)
            r0 = ((1 - IOR) / (1 + IOR)) ** 2
            fres = r0 + (1 - r0) * (1 - cosi) ** 5
            tir = k < 0
            reflect = tir | (rng.random(gi.size) < fres)
            refl = dg + 2 * cosi[:, None] * ng
            refr = eta[:, None] * dg + (eta * cosi - np.sqrt(np.clip(k, 0, None)))[
                :, None
            ] * ng
            newd = np.where(reflect[:, None], refl, refr)
            off = np.where(reflect[:, None], ng, -ng) * 1e-4
            o[gi] = p[gls] + off
            d[gi] = normalize(newd)
            count_emit[gi] = True

    return radiance.reshape(H, W, 3)


def tonemap(img):
    a, b, c, d_, e = 2.51, 0.03, 2.43, 0.59, 0.14
    x = img * 0.62
    x = np.clip((x * (a * x + b)) / (x * (c * x + d_) + e), 0, 1)
    return (np.power(x, 1 / 2.2) * 255 + 0.5).astype(np.uint8)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    acc = np.zeros((H, W, 3))
    for spp in range(1, CHECKPOINTS[-1] + 1):
        acc += trace_pass()
        if spp in CHECKPOINTS:
            img = Image.fromarray(tonemap(acc / spp))
            path = OUT / f"viewport-{spp}.jpg"
            img.save(path, quality=78 if spp < 64 else 86, optimize=True, progressive=True)
            print(f"spp {spp:4d} -> {path.name} ({path.stat().st_size // 1024} KB)", flush=True)


if __name__ == "__main__":
    main()
