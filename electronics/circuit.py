"""Stirrer motor power stage – SPICE netlist generator (ngspice).

Single source of truth for the circuit. Everything is plain text netlists built
from the parameters below, so the circuit can be diffed, reviewed and simulated
headless (`make sim`).

Circuit (see img/circuit_schematic.png):
  19 V laptop brick (90 W, ~4.7 A) -> fuse -> TVS + bulk cap -> motor (+)
  motor (-) -> low-side logic-level N-MOSFET -> 20 mΩ shunt -> GND
  Schottky flyback diode across the motor, 10 nF across the brushes.
  Arduino Nano: pot on A0 sets the PWM duty on D9 (20 kHz, Timer1).
  Shunt -> RC -> LM358 A (x22.4)   -> RC -> A1  (supply current, stall detection)
                 LM358 B comparator -> D2 (interrupt: over-current trip)
  Bus divider 100k/22k -> A2 (brick sagging / unplugged)

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

    # current sense
    r_shunt=0.020,      # 2 W metal strip / 2x 0.01 in series
    r_pf=1e3, c_pf=220e-9,      # pre-filter (~720 Hz) – removes 20 kHz chopping
    r_g1=2.2e3, r_g2=47e3,      # sense amp gain 1 + 47/2.2 = 22.4
    r_adc=1e3, c_adc=100e-9,    # ADC anti-alias / protection
    # over-current comparator: trip below the brick limit
    r_ref_top=10e3, r_ref_bot=6.2e3,   # 5 V * 6.2/16.2 = 1.91 V  -> ~4.3 A
    r_cmp_in=10e3, r_cmp_hys=1e6,      # ~35 mV hysteresis
    r_int=1e3,          # series into D2
    # bus voltage sense
    r_v1=100e3, r_v2=22e3, c_v=100e-9,  # 19 V -> 3.43 V, full scale 27.7 V
    # pot
    r_pot=10e3, c_pot=100e-9,
)


def trip_current(p=P):
    """Average supply current at which the comparator trips (rising)."""
    v_ref = p["v_logic"] * p["r_ref_bot"] / (p["r_ref_top"] + p["r_ref_bot"])
    gain = 1 + p["r_g2"] / p["r_g1"]
    return v_ref / gain / p["r_shunt"]


def steady_state(d, t_load, p=P):
    """Analytic steady state of the averaged model: (omega rad/s, I_motor A)."""
    vm = d * p["v_supply"]                      # ignores the small drops
    r, k = p["r_motor"] + d * d * (p["r_supply"] + p["r_shunt"]), p["ke"]
    # k*I = Tf + Tl + b*w ,  I = (vm - k*w)/r
    w = (k * vm / r - p["t_friction"] - t_load) / (k * k / r + p["b_visc"])
    w = max(w, 0.0)
    return w, (vm - k * w) / r


# ---------------------------------------------------------------- models
MODELS = """
* IRLZ44N-like logic-level MOSFET (55 V, ~22 mohm at Vgs 5 V) – approximate VDMOS
.model NMOS_LL VDMOS(Vto=1.7 Kp=40 Rd=8m Rs=6m Rb=10m Rg=2 lambda=0.01
+ Cgdmax=1.2n Cgdmin=80p a=0.4 Cgs=1.7n Cjo=0.9n Is=2e-12 ksubthres=0.1 bv=55)
* 40 V / 5..10 A Schottky (SB540 / MBR1045 class)
.model D_SCH D(Is=2e-5 N=1.05 Rs=0.015 Cjo=500p M=0.5 Vj=0.35 BV=45 Ibv=1m tt=0)
* SMBJ22A TVS
.model D_TVS D(Is=1e-12 N=1.5 Rs=0.3 BV={tvs_bv} Ibv=1m Cjo=600p)
.model D_CLAMP D(Is=1e-14 N=0.05)

* LM358 half: 1 MHz GBW, 0.5 V/us slew, output 0.02 .. Vcc-1.5 V
.subckt LM358 inp inn out
Bgm 0 int I = max(-5u, min(5u, 6.3e-5*(V(inp)-V(inn))))
Cc  int 0 10p
Ro  int 0 1.6G
Dh  int vh D_CLAMP
Vh  vh 0 3.5
Dl  vl int D_CLAMP
Vl  vl 0 0.02
Bo  ob 0 V = V(int)
Rob ob out 50
.ends
"""


def _pwl(points):
    return "PWL(" + " ".join(f"{t:.6g} {v:.6g}" for t, v in points) + ")"


def netlist(scenario, p=P):
    """scenario: dict(mode, duty=[(t,d)...], load=[(t,T)...], tstop, tmax,
    ic=dict(w=..., im=...) or None, save=[vectors], out=path)."""
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

    # ---- current sense + over-current comparator
    lines += [
        f"Rsh   sh 0 {p['r_shunt']}",
        f"Rpf   sh sf {p['r_pf']}",
        f"Cpf   sf 0 {p['c_pf']}",
        "XU1   sf fb aout LM358",
        f"Rg1   fb 0 {p['r_g1']}",
        f"Rg2   aout fb {p['r_g2']}",
        f"Radc  aout a1 {p['r_adc']}",
        f"Cadc  a1 0 {p['c_adc']}         ; -> Arduino A1",
        f"Rrt   v5 ref {p['r_ref_top']}",
        f"Rrb   ref 0 {p['r_ref_bot']}",
        "Cref  ref 0 100n",
        f"Rci   aout cp {p['r_cmp_in']}",
        f"Rch   cmp cp {p['r_cmp_hys']}",
        "XU2   cp ref cmp LM358",
        f"Rint  cmp d2 {p['r_int']}",
        "Cd2   d2 0 10p               ; -> Arduino D2 (INT0)",
        f"Rv1   bus a2 {p['r_v1']}",
        f"Rv2   a2 0 {p['r_v2']}",
        f"Cv    a2 0 {p['c_v']}          ; -> Arduino A2",
    ]

    # ---- analysis
    ics = []
    uic = ""
    if s.get("ic"):
        ics.append(f".ic V(w)={s['ic']['w']:.6g} V(bus)={p['v_supply']} V(cb)={p['v_supply']}"
                   f" V(ref)={p['v_logic'] * p['r_ref_bot'] / (p['r_ref_top'] + p['r_ref_bot']):.4g}"
                   f" V(a2)={p['v_supply'] * p['r_v2'] / (p['r_v1'] + p['r_v2']):.4g}")
        uic = " uic"
    lines += ics
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
    print(f"comparator trip ~ {trip_current():.2f} A supply current")
    for d in (0.3, 0.6, 0.99):
        w, i = steady_state(d, P["t_load"])
        print(f"d={d:.2f}: {w * 60 / 2 / math.pi:7.0f} rpm, I_motor {i:5.2f} A, "
              f"I_supply {d * i:5.2f} A")
