#!/usr/bin/env python3
"""Diagnostic movie for a hybrid P8 run, zoomed on the plume / ambient interface where the
runs abort (non-finite E once a near-vacuum gap opens and B runs away).

    python scripts/p8_diag_movie.py runs/P8/<ID> [--zmax-um 800] [--fps 6] [--out DIR]

One frame per ParticleHistogram2D dump (PH_*_zuz, every 25 steps), each paired with the
latest diag_fields dump at or before it (every 37 steps). Four panels on a shared z [um]:
  1. ion phase space z - v_z [km/s]: target ions orange, ambient blue (all tags summed)
  2. densities (log): n_e = rho/e, each ion species' n_e contribution, and the n_floor line
  3. B_y [T] (symlog) and j_z [A/m^2] (symlog, right axis)
  4. T_e [eV] (log) and E_z [V/m] (symlog, right axis)
"""
import argparse
import glob
import os
import re
import subprocess
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import yt  # noqa: E402

yt.set_log_level(40)
QE, C = 1.602176634e-19, 2.99792458e8


def used_inputs(run_dir):
    d = {}
    for line in open(os.path.join(run_dir, "warpx_used_inputs")):
        line = line.split("#", 1)[0].strip()
        if "=" in line:
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def load_ph(path, step):
    import openpmd_api as opmd
    s = opmd.Series(path, opmd.Access.read_only)
    it = s.iterations[step]
    m = it.meshes["data"]
    rc = m[opmd.Mesh_Record_Component.SCALAR]
    H = rc.load_chunk()
    s.flush()
    du, dz = m.grid_spacing
    u0, z0 = m.grid_global_offset
    nv, nz = H.shape
    out = (np.array(H), [z0, z0 + nz * dz, u0, u0 + nv * du])
    del s
    return out


def load_fields(path):
    ds = yt.load(path)
    ds.force_periodicity()
    cg = ds.covering_grid(0, ds.domain_left_edge, ds.domain_dimensions)
    nz = int(ds.domain_dimensions[0])
    z = np.linspace(float(ds.domain_left_edge[0]), float(ds.domain_right_edge[0]), nz + 1)
    zc = 0.5 * (z[1:] + z[:-1])
    f = {n[1]: np.asarray(cg["boxlib", n[1]]).reshape(nz) for n in ds.field_list}
    return zc, f, float(ds.current_time)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--zmax-um", type=float, default=800.0)
    ap.add_argument("--zmin-um", type=float, default=-100.0)
    ap.add_argument("--fps", type=int, default=6)
    ap.add_argument("--out", default=None)
    ap.add_argument("--ffmpeg", default=os.environ.get("FFMPEG", "ffmpeg"))
    args = ap.parse_args()

    rd = os.path.abspath(args.run_dir)
    rid = os.path.basename(rd)
    ui = used_inputs(rd)
    nfloor = float(ui.get("hybrid_pic_model.n_floor", "0").split()[0]) if \
        re.match(r"^[0-9.eE+-]+$", ui.get("hybrid_pic_model.n_floor", "x").split()[0]) else None
    species = ui["particles.species_names"].split()
    rf = os.path.join(rd, "diags", "reducedfiles")
    ph = {sp: os.path.join(rf, f"PH_{sp}_zuz", "openpmd_%06T.h5") for sp in species}
    ph_steps = sorted(int(re.search(r"(\d+)\.h5$", p).group(1))
                      for p in glob.glob(os.path.join(rf, f"PH_{species[0]}_zuz", "openpmd_*.h5")))
    fdumps = {int(p[-6:]): p for p in glob.glob(os.path.join(rd, "diags", "diag_fields*"))
              if p[-6:].isdigit()}
    fsteps = np.array(sorted(fdumps))
    last_step = 0
    log = os.path.join(rd, "run.log")
    if os.path.exists(log):
        st = re.findall(r"^STEP (\d+) ends", open(log, errors="ignore").read(), re.M)
        last_step = int(st[-1]) if st else 0
    aborted = os.path.exists(log) and "Non-finite value detected" in open(log, errors="ignore").read()
    print(f"{rid}: {len(ph_steps)} phase-space dumps, {len(fsteps)} field dumps, last step "
          f"{last_step}{' (ABORTED)' if aborted else ''}")

    frames = os.path.join(os.environ.get("MOVIE_SCRATCH", os.path.join(rd, ".frames")), rid, "p8diag")
    os.makedirs(frames, exist_ok=True)
    for f in glob.glob(os.path.join(frames, "frame_*.png")):
        os.remove(f)
    zlo, zhi = args.zmin_um, args.zmax_um
    for k, step in enumerate(ph_steps):
        fs = int(fsteps[max(0, np.searchsorted(fsteps, step, side="right") - 1)])
        zc, F, tf = load_fields(fdumps[fs])
        zum = zc * 1e6
        w = (zum >= zlo) & (zum <= zhi)
        fig, ax = plt.subplots(4, 1, figsize=(9, 11), sharex=True,
                               gridspec_kw={"height_ratios": [1.2, 1, 1, 1]})
        # 1. phase space
        rgb = None
        for role, col in (("targ", (1.0, 0.52, 0.22)), ("amb", (0.28, 0.72, 1.0))):
            Hs, ext = None, None
            for sp in species:
                if sp.startswith(role):
                    H, ext = load_ph(ph[sp], step)
                    Hs = H if Hs is None else Hs + H
            if Hs is None:
                continue
            zb = np.linspace(ext[0], ext[1], Hs.shape[1] + 1) * 1e6
            cols = (zb[:-1] >= zlo) & (zb[1:] <= zhi)
            Hw = Hs[:, cols]
            if rgb is None:
                rgb = np.zeros(Hw.shape + (3,))
            if Hw.max() > 0:
                a = 0.03 * Hw.max()
                inten = np.arcsinh(Hw / a) / np.arcsinh(Hw.max() / a)
                rgb += inten[..., None] * np.array(col)
            vext = [ext[2] * C / 1e3, ext[3] * C / 1e3]
            zext = [zb[:-1][cols][0], zb[1:][cols][-1]]
        if rgb is not None:
            ax[0].imshow(np.clip(rgb, 0, 1), origin="lower", aspect="auto",
                         extent=[zext[0], zext[1], vext[0], vext[1]], interpolation="nearest")
        ax[0].set_facecolor("#0b0b12")
        ax[0].set_ylabel(r"$v_z$ [km/s]")
        ax[0].text(0.01, 0.95, "target ions", color=(1, .52, .22), transform=ax[0].transAxes,
                   va="top", fontsize=8, weight="bold")
        ax[0].text(0.01, 0.86, "ambient ions", color=(.28, .72, 1), transform=ax[0].transAxes,
                   va="top", fontsize=8, weight="bold")
        # 2. densities
        ne = F.get("rho", np.zeros_like(zc)) / QE
        ax[1].semilogy(zum[w], np.maximum(ne[w], 1e18), "k", lw=1.2, label=r"$n_e=\rho/e$")
        for sp in species:
            r = F.get(f"rho_{sp}")
            if r is not None:
                col = ("tab:orange" if sp.startswith("targ") else
                       "0.5" if sp.startswith("bg") else "tab:blue")   # bg: immobile background
                ax[1].semilogy(zum[w], np.maximum(r[w] / QE, 1e18), lw=0.8, color=col,
                               ls="-" if sp.endswith(("C", "CH")) else "--", label=sp)
        if nfloor:
            ax[1].axhline(nfloor, color="r", lw=0.8, ls=":", label="n_floor")
        ax[1].set_ylim(1e20, 2e29)
        ax[1].set_ylabel(r"$n$ [m$^{-3}$]")
        ax[1].legend(fontsize=7, ncol=3, loc="upper right")
        # 3. B_y and j_z
        ax[2].plot(zum[w], F.get("By", np.zeros_like(zc))[w], "k", lw=1.2, label=r"$B_y$")
        ax[2].set_yscale("symlog", linthresh=10)
        ax[2].set_ylabel(r"$B_y$ [T]")
        a2 = ax[2].twinx()
        a2.plot(zum[w], F.get("jz", np.zeros_like(zc))[w], color="tab:green", lw=0.7)
        a2.set_yscale("symlog", linthresh=1e9)
        a2.set_ylabel(r"$j_z$ [A/m$^2$]", color="tab:green")
        # 4. T_e and E_z
        ax[3].semilogy(zum[w], np.maximum(F.get("Te", np.ones_like(zc))[w], 1.0), "k", lw=1.2)
        ax[3].set_ylabel(r"$T_e$ [eV]")
        a3 = ax[3].twinx()
        a3.plot(zum[w], F.get("Ez", np.zeros_like(zc))[w], color="tab:purple", lw=0.7)
        a3.set_yscale("symlog", linthresh=1e7)
        a3.set_ylabel(r"$E_z$ [V/m]", color="tab:purple")
        for x in ax:
            x.grid(alpha=0.25)
        ax[-1].set_xlabel(r"$z$ [$\mu$m]   (target face at 0, laser from the right)")
        ax[0].set_title(f"{rid}   step {step}  t = {step * float(ui['warpx.const_dt'].split()[0]) * 1e12:.0f} ps"
                        f"   (fields from step {fs})"
                        + (f"   [aborts at step {last_step}]" if aborted else ""), fontsize=9)
        fig.tight_layout()
        fig.savefig(os.path.join(frames, f"frame_{k:03d}.png"), dpi=100)
        plt.close(fig)
    out = args.out or os.path.join(rd, "media")
    os.makedirs(out, exist_ok=True)
    mp4 = os.path.join(out, f"{rid}_p8diag.mp4")
    subprocess.run([args.ffmpeg, "-y", "-loglevel", "error", "-framerate", str(args.fps),
                    "-i", os.path.join(frames, "frame_%03d.png"), "-c:v", "libx264",
                    "-crf", "20", "-pix_fmt", "yuv420p", mp4], check=True)
    print("wrote", mp4)


if __name__ == "__main__":
    main()
