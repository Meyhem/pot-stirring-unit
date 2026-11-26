"""Run all power-stage simulations with ngspice, check them, plot them.

  .venv/bin/python sim.py            # all scenarios -> out/ (data), ../img/circuit_*.png,
                                     # sim_results.md; exit code 1 if a check fails
Scenarios
  hard_start  pot jumps 0 -> 60 % with no soft start (what NOT to do)
  ramp_sweep  0 -> 99 % ramps of different length -> peak supply current
  soft_start  the chosen ramp (SOFT_START_S) to full speed, normal load
  stall       60 %, paddle jams at 1.5 s -> comparator trip vs brick shutdown
  switch60    real 20 kHz switching at 60 % (edges, losses), vs averaged model
"""

import math
import os
import subprocess
import sys

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from circuit import P, netlist, steady_state, trip_current  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
IMG = os.path.join(HERE, "..", "img")
SOFT_START_S = 2.5          # firmware ramp 0 -> 100 % [s]
V_IH = 3.0                  # AVR logic-high threshold at 5 V
AVG_WIN = 1e-3              # brick OCP assumed to react to a 1 ms average

AVG_SAVE = ["v(bus)", "i(vsrc)", "i(vam)", "v(w)", "v(a1)", "v(aout)",
            "v(d2)", "v(a2)", "v(d)", "v(tl)", "v(mlo)"]
SW_SAVE = AVG_SAVE + ["v(mst)", "v(gate)", "v(sh)", "i(vdm)", "i(vdf)", "v(pin)"]


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


def avg_sc(name, duty, load, tstop, tmax=100e-6, ic=None):
    return dict(name=name, mode="avg", duty=duty, load=load, tstop=tstop,
                tstep=tmax, tmax=tmax, ic=ic, save=AVG_SAVE)


TL = P["t_load"]
CHECKS = []      # (ok, text)
INFO = []


def check(ok, text):
    CHECKS.append((bool(ok), text))


def pins_ok(d, name):
    for k in ("v(a1)", "v(a2)", "v(d2)"):
        lo, hi = d[k].min(), d[k].max()
        check(-0.3 <= lo and hi <= 5.3,
              f"{name}: {k[2:-1].upper()} stays in -0.3..5.3 V (min {lo:.2f}, max {hi:.2f})")


# ------------------------------------------------------------------ scenarios
def sim_hard_start():
    d = run(avg_sc("hard_start", [(0, 0), (5e-3, 0), (5.01e-3, 0.6), (1, 0.6)],
                   [(0, TL), (1, TL)], 0.4, 20e-6))
    t, ia = moving_avg(d, "i_sup")
    INFO.append(f"hard_start: peak motor current {d['i(vam)'].max():.1f} A, "
                f"peak 1 ms supply current {ia.max():.1f} A "
                f"(brick {P['i_brick']} A) -> brick would shut down, "
                f"comparator trips at {first_above(d['time'], d['v(d2)'], V_IH) * 1e3:.2f} ms")
    check(first_above(d["time"], d["v(d2)"], V_IH) is not None,
          "hard_start: over-current comparator catches an un-ramped start")
    pins_ok(d, "hard_start")
    return d


def sim_ramp_sweep():
    rows = []
    for tr in (0.1, 0.25, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0):
        d = run(avg_sc(f"ramp_{tr:g}", [(0, 0), (0.02, 0), (0.02 + tr, 0.99), (9, 0.99)],
                       [(0, TL), (9, TL)], 0.02 + tr + 0.3, 200e-6))
        t, ia = moving_avg(d, "i_sup")
        rows.append((tr, d["i(vam)"].max(), ia.max(), d["v(d2)"].max() > V_IH))
    return rows


def sim_soft_start():
    d = run(avg_sc("soft_start", [(0, 0), (0.02, 0), (0.02 + SOFT_START_S, 0.99), (9, 0.99)],
                   [(0, TL), (9, TL)], SOFT_START_S + 0.6, 100e-6))
    t, ia = moving_avg(d, "i_sup")
    check(ia.max() < P["i_brick"],
          f"soft_start ({SOFT_START_S:g} s): 1 ms supply current peak {ia.max():.2f} A "
          f"< brick {P['i_brick']} A")
    check(d["v(d2)"].max() < V_IH,
          f"soft_start: comparator stays low at full speed (D2 max {d['v(d2)'].max():.2f} V)")
    w_ss, i_ss = steady_state(0.99, TL)
    rpm_end = d["rpm"][-1]
    check(abs(rpm_end - w_ss * 60 / 2 / math.pi) < 0.03 * w_ss * 60 / 2 / math.pi,
          f"soft_start: end speed {rpm_end:.0f} rpm matches analytic "
          f"{w_ss * 60 / 2 / math.pi:.0f} rpm (3 %)")
    INFO.append(f"full speed (99 %): {rpm_end:.0f} rpm motor, I_motor {d['i(vam)'][-1]:.2f} A, "
                f"I_supply {d['i_sup'][-1]:.2f} A, A1 = {d['v(a1)'][-1]:.2f} V, "
                f"A2 = {d['v(a2)'][-1]:.2f} V (bus {d['v(bus)'][-1]:.2f} V)")
    pins_ok(d, "soft_start")
    return d


T_JAM = 1.5


def sim_stall():
    d = run(avg_sc("stall", [(0, 0), (0.02, 0), (1.02, 0.6), (9, 0.6)],
                   [(0, TL), (T_JAM, TL), (T_JAM + 1e-3, P["t_jam"]), (9, P["t_jam"])],
                   T_JAM + 0.25, 50e-6))
    t, ia = moving_avg(d, "i_sup")
    t_trip = first_above(d["time"], d["v(d2)"], V_IH, T_JAM - 0.2)
    t_brick = first_above(t, ia, P["i_brick"], T_JAM - 0.2)
    pre = d["time"] < T_JAM - 0.01
    a1_run = d["v(a1)"][pre][-1]
    check(d["v(d2)"][pre].max() < V_IH, "stall: no trip while running normally at 60 %")
    check(t_trip is not None, "stall: comparator trips after the jam")
    if t_trip is not None:
        check(t_brick is None or t_trip < t_brick,
              f"stall: comparator trips {(t_trip - T_JAM) * 1e3:.1f} ms after the jam, "
              f"before the brick limit"
              + ("" if t_brick is None else f" ({(t_brick - T_JAM) * 1e3:.1f} ms)"))
    i_a1 = lambda v: v / (1 + P["r_g2"] / P["r_g1"]) / P["r_shunt"]  # noqa: E731
    INFO.append(f"stall: A1 {a1_run:.2f} V running ({i_a1(a1_run):.2f} A) -> "
                f"{d['v(a1)'].max():.2f} V jammed (LM358 rail; motor current "
                f"{d['i(vam)'].max():.1f} A if PWM is not cut)")
    pins_ok(d, "stall")
    return d, t_trip, t_brick


def sim_switch60():
    w0, i0 = steady_state(0.6, TL)
    ic = dict(w=w0, im=i0)
    duty = [(0, 0.6), (1, 0.6)]
    load = [(0, TL), (1, TL)]
    dsw = run(dict(name="switch60", mode="switch", duty=duty, load=load, tstop=3e-3,
                   tstep=10e-9, tmax=20e-9, ic=ic, save=SW_SAVE))
    davg = run(avg_sc("avg60", duty, load, 3e-3, 2e-6, ic=ic))
    per = 1 / P["f_pwm"]
    t0 = dsw["time"][-1] - 20 * per          # last 20 PWM periods
    m = dsw["time"] >= t0
    tt = dsw["time"][m]

    def mean(y):
        return np.trapezoid(y[m], tt) / (tt[-1] - tt[0])

    vds = dsw["v(mst)"] - dsw["v(sh)"]   # at the MOSFET pins
    p_fet = mean(vds * dsw["i(vdm)"])
    p_dio = mean((dsw["v(mlo)"] - dsw["v(bus)"]) * dsw["i(vdf)"])
    im_sw, im_avg = mean(dsw["i(vam)"]), davg["i(vam)"][-1]
    vm_sw = mean(dsw["v(bus)"] - dsw["v(mlo)"])
    vm_avg = davg["v(bus)"][-1] - davg["v(mlo)"][-1]
    vgs = dsw["v(gate)"] - dsw["v(sh)"]
    a1 = dsw["v(a1)"][m]
    check(vds.max() < 0.8 * 55, f"switch60: drain peak {vds.max():.1f} V < 44 V (80 % of 55 V)")
    check(vgs.max() < 5.2 and np.percentile(vgs[m], 70) > 4.5,
          f"switch60: gate fully on (Vgs on {np.percentile(vgs[m], 70):.2f} V, max {vgs.max():.2f} V)")
    check(p_fet < 1.0, f"switch60: MOSFET loss {p_fet * 1e3:.0f} mW < 1 W (no heatsink)")
    # a 0.23 ohm motor turns 1 % duty error (gate delay ~0.5 us of 50 us) into
    # ~0.8 A, so compare the motor VOLTAGE; the current difference is reported.
    check(abs(vm_sw - vm_avg) < 0.03 * vm_avg,
          f"switch60: switching vs averaged motor voltage {vm_sw:.2f} / {vm_avg:.2f} V (3 %)")
    INFO.append(f"switch60: motor current switching {im_sw:.2f} A vs averaged {im_avg:.2f} A "
                f"(gate turn-off delay stretches the duty slightly)")
    INFO.append(f"switch60: flyback diode loss {p_dio * 1e3:.0f} mW, motor ripple "
                f"{np.ptp(dsw['i(vam)'][m]):.2f} A p-p, A1 ripple {np.ptp(a1) * 1e3:.1f} mV p-p "
                f"({np.ptp(a1) / 5 * 1023:.1f} LSB), bus ripple {np.ptp(dsw['v(bus)'][m]) * 1e3:.0f} mV p-p")
    pins_ok(dsw, "switch60")
    return dsw


# ------------------------------------------------------------------ plots
def plot_start(hard, soft, sweep):
    fig, ax = plt.subplots(3, 1, figsize=(9, 9), sharex=False)
    for d, lab, c in ((hard, "hard start 0->60 %", "tab:red"),
                      (soft, f"soft start {SOFT_START_S:g} s 0->99 %", "tab:blue")):
        t, ia = moving_avg(d, "i_sup")
        ax[0].plot(t, ia, c, label=lab)
        ax[1].plot(d["time"], d["rpm"], c, label=lab)
    ax[0].axhline(P["i_brick"], color="k", ls="--", lw=1, label="brick 4.7 A")
    ax[0].axhline(trip_current(), color="tab:orange", ls=":", lw=1, label="comparator trip")
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


def plot_stall(d, t_trip, t_brick):
    m = d["time"] > T_JAM - 0.1
    t = d["time"][m]
    fig, ax = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
    ta, ia = moving_avg(d, "i_sup")
    ma = ta > T_JAM - 0.1
    ax[0].plot(t, d["i(vam)"][m], label="motor current")
    ax[0].plot(ta[ma], ia[ma], label="supply current (1 ms avg)")
    ax[0].axhline(P["i_brick"], color="k", ls="--", lw=1, label="brick 4.7 A")
    ax[0].set_ylabel("[A]")
    ax[0].legend(fontsize=8)
    ax[1].plot(t, d["rpm"][m], "tab:green")
    ax[1].set_ylabel("motor [rpm]")
    ax[2].plot(t, d["v(a1)"][m], label="A1 current sense")
    ax[2].plot(t, d["v(d2)"][m], label="D2 over-current")
    ax[2].axhline(V_IH, color="gray", ls=":", lw=1)
    ax[2].set_ylabel("[V]")
    ax[2].set_xlabel("time [s]")
    ax[2].legend(fontsize=8)
    for a in ax:
        a.axvline(T_JAM, color="tab:red", lw=1)
        if t_trip:
            a.axvline(t_trip, color="tab:orange", ls="--", lw=1)
        a.grid(alpha=0.3)
    fig.suptitle(f"Paddle jam at {T_JAM} s, 60 % duty (red = jam, orange = D2 trip)")
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "circuit_sim_stall.png"), dpi=90)


def plot_switch(d):
    per = 1 / P["f_pwm"]
    m = d["time"] >= d["time"][-1] - 3 * per
    t = (d["time"][m] - d["time"][m][0]) * 1e6
    fig, ax = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
    ax[0].plot(t, d["v(pin)"][m], label="Arduino D9")
    ax[0].plot(t, d["v(gate)"][m] - d["v(sh)"][m], label="Vgs")
    ax[0].set_ylabel("[V]")
    ax[0].legend(fontsize=8)
    ax[1].plot(t, d["v(mlo)"][m] - d["v(sh)"][m], "tab:red", label="Vds (motor -)")
    ax[1].plot(t, d["v(bus)"][m], "k", lw=0.8, label="bus")
    ax[1].set_ylabel("[V]")
    ax[1].legend(fontsize=8)
    ax[2].plot(t, d["i(vam)"][m], label="motor")
    ax[2].plot(t, d["i(vdm)"][m], label="MOSFET")
    ax[2].plot(t, d["i(vdf)"][m], label="flyback diode")
    ax[2].set_ylabel("[A]")
    ax[2].set_xlabel("time [us]")
    ax[2].legend(fontsize=8)
    for a in ax:
        a.grid(alpha=0.3)
    fig.suptitle("20 kHz switching at 60 % duty (steady state)")
    fig.tight_layout()
    fig.savefig(os.path.join(IMG, "circuit_sim_switching.png"), dpi=90)


def main():
    hard = sim_hard_start()
    sweep = sim_ramp_sweep()
    soft = sim_soft_start()
    stall, t_trip, t_brick = sim_stall()
    sw = sim_switch60()
    plot_start(hard, soft, sweep)
    plot_stall(stall, t_trip, t_brick)
    plot_switch(sw)

    lines = ["# Power stage – simulation results", "",
             "Generated by `electronics/sim.py` (ngspice). Do not edit by hand.", "",
             f"Comparator trip: {trip_current():.2f} A supply current "
             f"(brick {P['i_brick']} A).", "", "## Checks", ""]
    lines += [f"- {'PASS' if ok else '**FAIL**'} – {txt}" for ok, txt in CHECKS]
    lines += ["", "## Soft-start ramp sweep (0 -> 99 %)", "",
              "| ramp [s] | peak motor A | peak supply A (1 ms avg) | comparator trips |",
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
