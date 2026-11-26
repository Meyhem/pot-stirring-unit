"""Run all power-stage simulations with ngspice, check them, plot them.

  .venv/bin/python sim.py            # all scenarios -> out/ (data), ../img/circuit_*.png,
                                     # sim_results.md; exit code 1 if a check fails
Scenarios
  hard_start  pot jumps 0 -> 60 % with no soft start (what NOT to do)
  ramp_sweep  0 -> 99 % ramps of different length -> peak supply current
  soft_start  the chosen ramp (SOFT_START_S) to full speed, normal load
  stall_60 / stall_30 / stall_99   paddle jams at 60 / 30 / 99 % duty
  switch60    real 20 kHz switching at 60 % (edges, losses), vs averaged model

Stall detection is the firmware rule in circuit.STALL, applied here to the
simulated A1 voltage sampled like the ADC would (no comparator in hardware).
"""

import math
import os
import subprocess
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from circuit import P, STALL, adc_counts, netlist, steady_state  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
IMG = os.path.join(HERE, "..", "img")
SOFT_START_S = 2.5          # firmware ramp 0 -> 99 % [s]
AVG_WIN = 1e-3              # brick OCP assumed to react to a 1 ms average
SHUNT_RATING = 5.0          # W

AVG_SAVE = ["v(bus)", "i(vsrc)", "i(vam)", "v(w)", "v(a1)", "v(sh)", "v(d)", "v(tl)", "v(mlo)"]
SW_SAVE = AVG_SAVE + ["v(mst)", "v(gate)", "i(vdm)", "i(vdf)", "v(pin)"]

TL = P["t_load"]
CHECKS = []      # (ok, text)
INFO = []


def check(ok, text):
    CHECKS.append((bool(ok), text))


def run(sc):
    os.makedirs(OUT, exist_ok=True)
    sc["out"] = os.path.join(OUT, sc["name"] + ".txt")
    cir = os.path.join(OUT, sc["name"] + ".cir")
    with open(cir, "w") as f:
        f.write(netlist(sc))
    r = subprocess.run(["ngspice", "-b", cir], capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(sc["out"]):
        sys.exit(f"ngspice failed on {sc['name']}:\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
    with open(sc["out"]) as f:
        names = f.readline().split()
    data = np.loadtxt(sc["out"], skiprows=1)
    d = {n.lower(): data[:, i] for i, n in enumerate(names)}
    d["i_sup"] = -d["i(vsrc)"]
    d["rpm"] = d["v(w)"] * 60 / (2 * math.pi)
    return d


def uniform(d, key, dt):
    t = np.arange(d["time"][0], d["time"][-1], dt)
    return t, np.interp(t, d["time"], d[key])


def moving_avg(d, key, win=AVG_WIN, dt=20e-6):
    t, y = uniform(d, key, dt)
    n = max(1, int(win / dt))
    return t, np.convolve(y, np.ones(n) / n)[:len(y)]     # causal, like an OCP filter


def first_above(t, y, thr, t_from=0.0):
    idx = np.where((y > thr) & (t >= t_from))[0]
    return t[idx[0]] if len(idx) else None


def at(d, key, t):
    return float(np.interp(t, d["time"], d[key]))


def detect(d, t_from=0.0):
    """Firmware stall rule on sampled A1. Returns (t_detect or None, t, i_sup, i_mot)."""
    t = np.arange(d["time"][0], d["time"][-1], STALL["t_sample"])
    a1 = np.interp(t, d["time"], d["v(a1)"])
    a1 = np.round(adc_counts(a1)) * 5.0 / 1023                 # 10-bit quantisation
    duty = np.interp(t, d["time"], d["v(d)"])
    i_sup = a1 / P["r_shunt"]
    i_mot = np.where(duty >= STALL["d_min"], i_sup / np.maximum(duty, 1e-3), 0.0)
    over = (i_sup > STALL["i_supply"]) | (i_mot > STALL["i_motor"])
    run_len = 0
    for tk, o in zip(t, over):
        run_len = run_len + 1 if o else 0
        if run_len >= STALL["n_confirm"] and tk >= t_from:
            return tk, t, i_sup, i_mot
    return None, t, i_sup, i_mot


def avg_sc(name, duty, load, tstop, tmax=100e-6, ic=None):
    return dict(name=name, mode="avg", duty=duty, load=load, tstop=tstop,
                tstep=tmax, tmax=tmax, ic=ic, save=AVG_SAVE)


def pin_ok(d, name):
    lo, hi = d["v(a1)"].min(), d["v(a1)"].max()
    check(-0.3 <= lo and hi <= 5.3, f"{name}: A1 stays in -0.3..5.3 V (min {lo:.2f}, max {hi:.2f})")


def shunt_power(d, m):
    """Average shunt dissipation in the averaged model: d * Im^2 * R."""
    im, du = d["i(vam)"][m], d["v(d)"][m]
    return float(np.mean(du * im * im)) * P["r_shunt"]


# ------------------------------------------------------------------ scenarios
def sim_hard_start():
    d = run(avg_sc("hard_start", [(0, 0), (5e-3, 0), (5.01e-3, 0.6), (1, 0.6)],
                   [(0, TL), (1, TL)], 0.4, 20e-6))
    t, ia = moving_avg(d, "i_sup")
    td, *_ = detect(d)
    INFO.append(f"hard_start: peak motor current {d['i(vam)'].max():.1f} A, "
                f"peak 1 ms supply current {ia.max():.1f} A (brick {P['i_brick']} A) – "
                f"the brick shuts down before firmware can react: soft-start is mandatory")
    check(td is not None, f"hard_start: stall rule fires on an un-ramped start "
                          f"({(td or 0) * 1e3:.0f} ms)")
    pin_ok(d, "hard_start")
    return d


def sim_ramp_sweep():
    rows = []
    for tr in (0.25, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0):
        d = run(avg_sc(f"ramp_{tr:g}", [(0, 0), (0.02, 0), (0.02 + tr, 0.99), (9, 0.99)],
                       [(0, TL), (9, TL)], 0.02 + tr + 0.3, 200e-6))
        t, ia = moving_avg(d, "i_sup")
        td, *_ = detect(d)
        rows.append((tr, d["i(vam)"].max(), ia.max(), td is not None))
    return rows


def sim_soft_start():
    d = run(avg_sc("soft_start", [(0, 0), (0.02, 0), (0.02 + SOFT_START_S, 0.99), (9, 0.99)],
                   [(0, TL), (9, TL)], SOFT_START_S + 0.6, 100e-6))
    t, ia = moving_avg(d, "i_sup")
    td, ts, isup, imot = detect(d)
    check(ia.max() < P["i_brick"],
          f"soft_start ({SOFT_START_S:g} s): 1 ms supply current peak {ia.max():.2f} A "
          f"< brick {P['i_brick']} A")
    check(td is None, f"soft_start: no false stall detection (estimated motor current max "
                      f"{imot.max():.2f} A < {STALL['i_motor']} A, supply {isup.max():.2f} A "
                      f"< {STALL['i_supply']} A)")
    w_ss, _ = steady_state(0.99, TL)
    rpm_ss = w_ss * 60 / 2 / math.pi
    check(abs(d["rpm"][-1] - rpm_ss) < 0.03 * rpm_ss,
          f"soft_start: end speed {d['rpm'][-1]:.0f} rpm matches analytic {rpm_ss:.0f} rpm (3 %)")
    end = d["time"] > d["time"][-1] - 0.1
    p_sh = shunt_power(d, end)
    check(p_sh < 0.5 * SHUNT_RATING,
          f"soft_start: shunt {p_sh:.2f} W at full speed < 50 % of {SHUNT_RATING:g} W")
    INFO.append(f"full speed (99 %): {d['rpm'][-1]:.0f} rpm motor, I_motor {d['i(vam)'][-1]:.2f} A, "
                f"I_supply {d['i_sup'][-1]:.2f} A, A1 {d['v(a1)'][-1]:.3f} V = "
                f"{adc_counts(d['v(a1)'][-1]):.0f} counts, shunt {p_sh:.2f} W "
                f"(continuous at the 4.7 A brick limit: {4.7 * 4.7 * P['r_shunt']:.1f} W)")
    pin_ok(d, "soft_start")
    return d


def sim_stall(duty):
    """Soft-start to `duty` (same slope as SOFT_START_S), run, then jam the paddle."""
    name = f"stall_{round(duty * 100)}"
    t_ramp = 0.02 + SOFT_START_S * duty / 0.99
    t_jam = t_ramp + 0.5
    d = run(avg_sc(name, [(0, 0), (0.02, 0), (t_ramp, duty), (99, duty)],
                   [(0, TL), (t_jam, TL), (t_jam + 1e-3, P["t_jam"]), (99, P["t_jam"])],
                   t_jam + 0.25, 50e-6))
    t, ia = moving_avg(d, "i_sup")
    td, ts, isup, imot = detect(d)
    t_brick = first_above(t, ia, P["i_brick"], t_jam - 0.2)
    check(td is not None and td > t_jam,
          f"{name}: no detection while running, detected after the jam"
          + (f" (+{(td - t_jam) * 1e3:.1f} ms)" if td else ""))
    if td is not None and t_brick is not None and td > t_jam:
        check(td <= t_brick + 1e-3,
              f"{name}: detected at +{(td - t_jam) * 1e3:.1f} ms, brick limit reached at "
              f"+{(t_brick - t_jam) * 1e3:.1f} ms (at most 1 ms later)")
    a1_run = at(d, "v(a1)", t_jam - 1e-3)
    INFO.append(f"{name}: running A1 {adc_counts(a1_run):.0f} counts "
                f"({a1_run / P['r_shunt'] / duty:.2f} A motor); jammed motor current "
                f"{d['i(vam)'].max():.1f} A if PWM is not cut; brick limit "
                + (f"+{(t_brick - t_jam) * 1e3:.1f} ms" if t_brick else "not reached"))
    pin_ok(d, name)
    return dict(d=d, td=td, t_brick=t_brick, ts=ts, isup=isup, imot=imot, duty=duty, t_jam=t_jam)


def sim_switch60():
    w0, i0 = steady_state(0.6, TL)
    ic = dict(w=w0, im=i0, a1=0.6 * i0 * P["r_shunt"])
    duty = [(0, 0.6), (1, 0.6)]
    load = [(0, TL), (1, TL)]
    dsw = run(dict(name="switch60", mode="switch", duty=duty, load=load, tstop=6e-3,
                   tstep=10e-9, tmax=20e-9, ic=ic, save=SW_SAVE))
    davg = run(avg_sc("avg60", duty, load, 6e-3, 2e-6, ic=ic))
    per = 1 / P["f_pwm"]
    m = dsw["time"] >= dsw["time"][-1] - 20 * per          # last 20 PWM periods
    tt = dsw["time"][m]

    def mean(y):
        return np.trapezoid(y[m], tt) / (tt[-1] - tt[0])

    vds = dsw["v(mst)"] - dsw["v(sh)"]
    vgs = dsw["v(gate)"] - dsw["v(sh)"]
    p_fet = mean(vds * dsw["i(vdm)"])
    p_dio = mean((dsw["v(mlo)"] - dsw["v(bus)"]) * dsw["i(vdf)"])
    p_sh = mean(dsw["i(vdm)"] ** 2) * P["r_shunt"]
    vm_sw = mean(dsw["v(bus)"] - dsw["v(mlo)"])
    vm_avg = davg["v(bus)"][-1] - davg["v(mlo)"][-1]
    a1 = dsw["v(a1)"][m]
    on = np.percentile(vgs[m], 75)
    check(vds.max() < 0.8 * 55, f"switch60: drain peak {vds.max():.1f} V < 44 V (80 % of 55 V)")
    check(on > 4.0 and vgs.max() < 16,
          f"switch60: gate on {on:.2f} V (> 4 V; the shunt lifts the source), max {vgs.max():.2f} V")
    check(p_fet < 1.0, f"switch60: MOSFET loss {p_fet * 1e3:.0f} mW < 1 W (no heatsink)")
    check(abs(vm_sw - vm_avg) < 0.03 * vm_avg,
          f"switch60: switching vs averaged motor voltage {vm_sw:.2f} / {vm_avg:.2f} V (3 %)")
    check(adc_counts(np.ptp(a1)) < 4,
          f"switch60: A1 ripple {adc_counts(np.ptp(a1)):.1f} counts p-p < 4")
    INFO.append(f"switch60: diode {p_dio * 1e3:.0f} mW, shunt {p_sh * 1e3:.0f} mW; source (shunt top) "
                f"swings {dsw['v(sh)'][m].min():.2f} .. {dsw['v(sh)'][m].max():.2f} V "
                f"({P['l_shunt'] * 1e6:g} uH shunt inductance); motor ripple "
                f"{np.ptp(dsw['i(vam)'][m]):.2f} A p-p, bus ripple {np.ptp(dsw['v(bus)'][m]) * 1e3:.0f} mV p-p")
    pin_ok(dsw, "switch60")
    return dsw


# ------------------------------------------------------------------ plots
def plot_start(hard, soft, sweep):
    fig, ax = plt.subplots(3, 1, figsize=(9, 9))
    for d, lab, c in ((hard, "hard start 0->60 %", "tab:red"),
                      (soft, f"soft start {SOFT_START_S:g} s 0->99 %", "tab:blue")):
        t, ia = moving_avg(d, "i_sup")
        ax[0].plot(t, ia, c, label=lab)
        ax[1].plot(d["time"], d["rpm"], c, label=lab)
    ax[0].axhline(P["i_brick"], color="k", ls="--", lw=1, label="brick 4.7 A")
    ax[0].axhline(STALL["i_supply"], color="tab:orange", ls=":", lw=1, label="firmware supply limit")
    ax[0].set_ylabel("supply current, 1 ms avg [A]")
    ax[0].set_ylim(0, 15)
    ax[0].legend(fontsize=8)
    ax[1].set_ylabel("motor speed [rpm]")
    ax[1].set_xlabel("time [s]")
    ax[1].legend(fontsize=8)
    tr = [r[0] for r in sweep]
    ax[2].plot(tr, [r[2] for r in sweep], "o-", label="peak supply current (1 ms avg)")
    ax[2].axhline(P["i_brick"], color="k", ls="--", lw=1)
    ax[2].axvline(SOFT_START_S, color="tab:blue", ls=":", lw=1, label="chosen ramp")
    ax[2].set_xlabel("soft-start ramp 0 -> 99 % [s]")
    ax[2].set_ylabel("[A]")
    ax[2].legend(fontsize=8)
    for a in ax:
        a.grid(alpha=0.3)
    fig.suptitle("Start-up from the 19 V / 4.7 A brick")
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "circuit_sim_startup.png"), dpi=90)
    plt.close(fig)


def plot_stall(runs):
    fig, ax = plt.subplots(3, len(runs), figsize=(5 * len(runs), 8), sharex=True)
    for col, r in enumerate(runs):
        d, tj = r["d"], r["t_jam"]
        m = d["time"] > tj - 0.05
        t = d["time"][m]
        ta, ia = moving_avg(d, "i_sup")
        ma = ta > tj - 0.05
        mm = r["ts"] > tj - 0.05
        a = ax[0, col]
        a.plot(t, d["i(vam)"][m], label="motor current")
        a.plot(ta[ma], ia[ma], label="supply current (1 ms avg)")
        a.axhline(P["i_brick"], color="k", ls="--", lw=1, label="brick 4.7 A")
        a.set_title(f"jam at {r['duty'] * 100:.0f} % duty")
        a.set_ylabel("[A]")
        a.legend(fontsize=7)
        ax[1, col].plot(t, d["rpm"][m], "tab:green")
        ax[1, col].set_ylabel("motor [rpm]")
        a = ax[2, col]
        a.step(r["ts"][mm], r["imot"][mm], where="post", label="firmware: motor A (A1 / duty)")
        a.step(r["ts"][mm], r["isup"][mm], where="post", label="firmware: supply A (A1 / R)")
        a.axhline(STALL["i_motor"], color="tab:blue", ls=":", lw=1)
        a.axhline(STALL["i_supply"], color="tab:orange", ls=":", lw=1)
        a.set_ylabel("[A] from ADC")
        a.set_xlabel("time [s]")
        a.set_ylim(0, 3 * STALL["i_motor"])
        a.legend(fontsize=7)
        for a in ax[:, col]:
            a.axvline(tj, color="tab:red", lw=1)
            if r["td"]:
                a.axvline(r["td"], color="tab:purple", ls="--", lw=1)
            a.grid(alpha=0.3)
    fig.suptitle("Paddle jam (red) and firmware detection from A1 (purple)")
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "circuit_sim_stall.png"), dpi=90)
    plt.close(fig)


def plot_switch(d):
    per = 1 / P["f_pwm"]
    m = d["time"] >= d["time"][-1] - 3 * per
    t = (d["time"][m] - d["time"][m][0]) * 1e6
    fig, ax = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
    ax[0].plot(t, d["v(pin)"][m], label="Arduino D9")
    ax[0].plot(t, d["v(gate)"][m] - d["v(sh)"][m], label="Vgs")
    ax[0].plot(t, d["v(sh)"][m], label="source = shunt top")
    ax[0].set_ylabel("[V]")
    ax[0].legend(fontsize=8)
    ax[1].plot(t, d["v(mst)"][m] - d["v(sh)"][m], "tab:red", label="Vds")
    ax[1].plot(t, d["v(bus)"][m], "k", lw=0.8, label="bus")
    ax[1].set_ylabel("[V]")
    ax[1].legend(fontsize=8)
    ax[2].plot(t, d["i(vam)"][m], label="motor")
    ax[2].plot(t, d["i(vdm)"][m], label="MOSFET = shunt")
    ax[2].plot(t, d["i(vdf)"][m], label="flyback diode")
    ax[2].set_ylabel("[A]")
    ax[2].set_xlabel("time [us]")
    ax[2].legend(fontsize=8)
    for a in ax:
        a.grid(alpha=0.3)
    fig.suptitle("20 kHz switching at 60 % duty (steady state)")
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "circuit_sim_switching.png"), dpi=90)
    plt.close(fig)


def main():
    hard = sim_hard_start()
    sweep = sim_ramp_sweep()
    soft = sim_soft_start()
    stalls = [sim_stall(x) for x in (0.6, 0.3, 0.99)]
    sw = sim_switch60()
    plot_start(hard, soft, sweep)
    plot_stall(stalls[:2])
    plot_switch(sw)

    lines = ["# Power stage – simulation results", "",
             "Generated by `electronics/sim.py` (ngspice). Do not edit by hand.", "",
             f"Shunt {P['r_shunt']} Ω → A1 = {P['r_shunt']} V/A of supply current "
             f"({adc_counts(P['r_shunt']):.0f} counts/A). Firmware stall rule: sample every "
             f"{STALL['t_sample'] * 1e3:g} ms, {STALL['n_confirm']} samples over "
             f"{STALL['i_supply']} A supply or {STALL['i_motor']} A motor (= supply / duty).",
             "", "## Checks", ""]
    lines += [f"- {'PASS' if ok else '**FAIL**'} – {txt}" for ok, txt in CHECKS]
    lines += ["", "## Soft-start ramp sweep (0 -> 99 %)", "",
              "| ramp [s] | peak motor A | peak supply A (1 ms avg) | stall rule fires |",
              "|---|---|---|---|"]
    lines += [f"| {tr:g} | {im:.1f} | {ia:.2f} | {'yes' if tp else 'no'} |"
              for tr, im, ia, tp in sweep]
    lines += ["", "## Notes", ""] + [f"- {x}" for x in INFO] + [""]
    with open(os.path.join(HERE, "sim_results.md"), "w") as f:
        f.write("\n".join(lines))
    print("\n".join(lines))
    sys.exit(0 if all(ok for ok, _ in CHECKS) else 1)


if __name__ == "__main__":
    main()
