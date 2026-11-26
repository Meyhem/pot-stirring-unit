"""Stirrer motor power stage – SPICE netlist generator (ngspice).

Single source of truth for the circuit. Everything is plain text netlists built
from the parameters below, so the circuit can be diffed, reviewed and simulated
headless (`make circuit`).

Circuit (see img/circuit_schematic.png) – the simple version, no op-amp:
  19 V laptop brick (90 W, ~4.7 A) -> fuse -> TVS + bulk cap -> motor (+)
  motor (-) -> low-side logic-level N-MOSFET -> 0.15 ohm / 5 W shunt -> GND
  Schottky flyback diode across the motor, 10 nF across the brushes.
  Arduino Nano: pot on A0 sets the PWM duty on D9 (20 kHz, Timer1).
  10 uF ceramic across the shunt. Shunt -> 10k / 47 nF -> A1. The shunt only carries current while the MOSFET
  is on, so A1 = R_shunt * supply current; firmware gets motor current = that / duty.
  Stall / over-current detection is firmware (STALL below), no comparator.

Two model levels:
  mode="avg"    – duty-cycle averaged switch (seconds of simulated time: start-up,
                  stall); the shunt sees d * I_motor like the real chopped current.
  mode="switch" – real MOSFET + diode + 20 kHz PWM (a few ms: edges, losses).
"""

import math

# ---------------------------------------------------------------- parameters
P = dict(
    # supply: laptop brick, 19 V / 90 W. OCP of such bricks is a bit above rating.
    v_supply=19.0,
    r_supply=0.05,      # brick output + cable resistance [ohm]
    l_cable=2e-6,       # cable inductance [H]
    i_brick=4.7,        # rated current; staying below it = no brick shutdown [A]
    r_fuse=0.01,        # 5 A slow fuse (not modelled as blowing)
    c_bulk=1000e-6,     # bulk electrolytic, 35 V low-ESR
    esr_bulk=0.025,
    tvs_bv=24.4,        # SMBJ22A breakdown (22 V stand-off, clamps ~35 V)

    # motor: RS-550 class, TOPOWER 550-18V. Estimated from typical RS-550 18 V
    # data (no-load ~19k rpm / 1.4 A, stall ~78 A) – MEASURE R and no-load current.
    r_motor=0.23,       # armature resistance [ohm]
    l_motor=100e-6,     # armature inductance [H]
    ke=0.0088,          # back-EMF = torque constant [V*s/rad] = [N*m/A]
    j_rotor=1.0e-5,     # rotor + drill gearbox reflected inertia [kg*m^2]
    t_friction=0.0123,  # Coulomb friction (no-load current * ke) [N*m]
    b_visc=1e-7,        # viscous friction [N*m*s/rad]
    t_load=0.015,       # stirring load at the MOTOR shaft (after drill + bevel gears) [N*m]
    t_jam=0.30,         # jammed paddle at the motor shaft [N*m]
    c_motor=10e-9,      # ceramic across the brushes (EMI). 100 nF is recharged
                        # every PWM edge: +0.2 W in the MOSFET at 20 kHz
    l_stray=30e-9,      # wiring inductance in the MOSFET/diode loop (keep it short)

    # switch + flyback
    f_pwm=20e3,         # Arduino Timer1, ICR1 = 799 -> 20 kHz (inaudible)
    r_pin=25.0,         # AVR output pin resistance
    r_gate=100.0,       # gate series resistor (limits pin current)
    r_gate_pd=10e3,     # gate pull-down (motor off while Arduino boots)
    v_logic=5.0,

    # current sense: the 0.15R 5 W cement resistor the user has
    r_shunt=0.15,
    l_shunt=1e-6,       # wire-wound cement resistor: ~0.5..2 uH, 1 uH assumed
    c_shunt=10e-6,      # ceramic across the shunt: takes the PWM edges, so the shunt's
                        # inductance can't kick the MOSFET source (1.34 W -> 0.34 W)
    r_sense=10e3,       # series into A1: limits pin clamp current (~0.2 mA at 7 V)
    c_sense=47e-9,      # 10k * 47n = 0.47 ms: removes the 20 kHz chopping
    # pot
    r_pot=10e3, c_pot=100e-9,
)

# Detection rule the firmware will use (sim.py checks that the A1 signal supports it):
# sample A1 every 1 ms; supply current = A1 / r_shunt, motor current = that / duty.
STALL = dict(
    t_sample=0.5e-3,    # A1 sample period [s]
    n_confirm=2,        # consecutive samples over a limit -> cut PWM
    i_supply=4.2,       # supply-current limit [A] (protects the 4.7 A brick)
    i_motor=8.0,        # motor-current limit [A] (jam; normal ~3 A, ramp ~4 A)
    d_min=0.10,         # below this duty the motor-current estimate is not used
)


def adc_counts(v, vref=5.0):
    return v / vref * 1023


def steady_state(d, t_load, p=P):
    """Analytic steady state of the averaged model: (omega rad/s, I_motor A)."""
    vm = d * p["v_supply"]                      # ignores the small drops
    r, k = p["r_motor"] + d * (p["r_supply"] + p["r_shunt"]), p["ke"]
    # k*I = Tf + Tl + b*w ,  I = (vm - k*w)/r
    w = (k * vm / r - p["t_friction"] - t_load) / (k * k / r + p["b_visc"])
    w = max(w, 0.0)
    return w, (vm - k * w) / r


# ---------------------------------------------------------------- models
MODELS = """
* IRLZ44N-like logic-level MOSFET (55 V, ~22 mohm at Vgs 5 V) – approximate VDMOS
.model NMOS_LL VDMOS(Vto=1.7 Kp=40 Rd=8m Rs=6m Rb=10m Rg=2 lambda=0.01
+ Cgdmax=1.2n Cgdmin=80p a=0.4 Cgs=1.7n Cjo=0.9n Is=2e-12 ksubthres=0.1 bv=55)
* 40 V / 5 A Schottky (SB540 class)
.model D_SCH D(Is=2e-5 N=1.05 Rs=0.015 Cjo=500p M=0.5 Vj=0.35 BV=45 Ibv=1m tt=0)
* SMBJ22A TVS
.model D_TVS D(Is=1e-12 N=1.5 Rs=0.3 BV={tvs_bv} Ibv=1m Cjo=600p)
* AVR input protection diodes (to 5 V and GND)
.model D_PIN D(Is=1e-12 N=1.3 Rs=50)
"""


def _pwl(points):
    return "PWL(" + " ".join(f"{t:.6g} {v:.6g}" for t, v in points) + ")"


def netlist(scenario, p=P):
    """scenario: dict(name, mode, duty=[(t,d)...], load=[(t,T)...], tstop, tstep,
    tmax, ic=dict(w=..., im=...) or None, save=[vectors], out=path)."""
    s = scenario
    sw = s["mode"] == "switch"
    lines = [f"* stirrer power stage – {s['name']} ({s['mode']})"]
    lines.append(MODELS.format(**p))

    # ---- supply, protection, bulk
    lines += [
        f"Vsrc  src 0 DC {p['v_supply']}",
        f"Rsrc  src s1 {p['r_supply']}",
        f"Lcab  s1 s2 {p['l_cable']}",
        f"Rfuse s2 bus {p['r_fuse']}",
        "Dtvs  0 bus D_TVS",
        f"Cbulk bus cb {p['c_bulk']}",
        f"Rbulk cb 0 {p['esr_bulk']}",
        f"V5    v5 0 DC {p['v_logic']}   ; buck module 19 V -> 5 V (ideal here)",
    ]

    # ---- motor (electrical + mechanical analogue: V(w) = omega in rad/s)
    im0 = s["ic"]["im"] if s.get("ic") else 0
    lines += [
        f"Ra    bus ma {p['r_motor']}",
        f"La    ma mb {p['l_motor']} IC={im0}",
        "Vam   mb mc 0                 ; motor current ammeter",
        f"Bemf  mc mlo V = {p['ke']}*V(w)",
        f"Cm    bus mlo {p['c_motor']}",
        f"Bt    0 w I = {p['ke']}*I(Vam)",
        f"Cj    w 0 {p['j_rotor']}",
        f"Bfr   w 0 I = ({p['t_friction']}+V(tl))*tanh(V(w)/5) + {p['b_visc']}*V(w)",
        f"Vtl   tl 0 {_pwl(s['load'])}",
        f"Vd    d 0 {_pwl(s['duty'])}      ; PWM duty = pot position",
    ]

    if sw:
        per = 1 / p["f_pwm"]
        lines += [
            f"Vsaw  saw 0 PULSE(0 1 0 {per - 0.1e-6:.6g} 0.1u 0 {per:.6g})",
            f"Bpin  pin 0 V = {p['v_logic'] / 2}*(1+tanh(300*(V(d)-V(saw))))  ; Arduino D9",
            f"Rpin  pin gdrv {p['r_pin']}",
            f"Rg    gdrv gate {p['r_gate']}",
            f"Rgpd  gate 0 {p['r_gate_pd']}",
            f"Lstr  mlo mst {p['l_stray']}",
            "Vdm   mst mdr 0               ; MOSFET drain ammeter",
            "M1    mdr gate sh NMOS_LL",
            "Vdf   mlo dfa 0               ; flyback diode ammeter",
            "Dfw   dfa bus D_SCH",
        ]
    else:
        # averaged low-side switch: motor low side sits at (1-d)*(Vbus+Vf),
        # bus gets the free-wheel share (1-d)*Im back -> shunt sees d*Im.
        lines += [
            "Vsw   mlo mlo2 0",
            "Bsw   mlo2 sh V = (1-V(d))*(V(bus)+0.45-V(sh))",
            "Bfw   sh bus I = (1-V(d))*I(Vsw)",
            "Bpin  pin 0 V = 0",
            "Vgate gate 0 0",
        ]

    # ---- shunt + sense RC into A1 (with the AVR's pin clamp diodes)
    lines += [
        f"Lsh   sh shm {p['l_shunt']}",
        f"Rsh   shm 0 {p['r_shunt']}",
    ] + ([f"Csh   sh 0 {p['c_shunt']}"] if p["c_shunt"] > 0 else []) + [
        f"Rsen  sh a1 {p['r_sense']}",
        f"Csen  a1 0 {p['c_sense']}         ; -> Arduino A1",
        "Dph   a1 v5 D_PIN",
        "Dpl   0 a1 D_PIN",
    ]

    # ---- analysis
    uic = ""
    if s.get("ic"):
        lines.append(f".ic V(w)={s['ic']['w']:.6g} V(bus)={p['v_supply']} V(cb)={p['v_supply']}"
                     + (f" V(a1)={s['ic']['a1']:.6g}" if "a1" in s["ic"] else ""))
        uic = " uic"
    lines += [
        ".options method=gear reltol=1e-3 abstol=1e-9 vntol=1e-5 itl4=50",
        ".control",
        "set wr_singlescale",
        "set wr_vecnames",
        "option numdgt=7",
        f"tran {s['tstep']} {s['tstop']} 0 {s['tmax']}{uic}",
        f"wrdata {s['out']} " + " ".join(s["save"]),
        "quit",
        ".endc",
        ".end",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    for d in (0.3, 0.6, 0.99):
        w, i = steady_state(d, P["t_load"])
        a1 = d * i * P["r_shunt"]
        print(f"d={d:.2f}: {w * 60 / 2 / math.pi:7.0f} rpm, I_motor {i:5.2f} A, "
              f"I_supply {d * i:5.2f} A, A1 {a1:.3f} V = {adc_counts(a1):.0f} counts")
