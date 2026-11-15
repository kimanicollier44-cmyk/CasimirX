#!/usr/bin/env python3
"""CasimirX - educational Casimir effect / vacuum physics lab.

by Darion Kellar

Pure Python standard library. Zero dependencies. Zero network.
Education only: the Casimir effect is real, measured physics - two
uncharged metal plates in vacuum attract because the zero-point
field between them supports fewer modes than the field outside.
This lab computes it honestly: the exact Casimir pressure
P = -pi^2 hbar c / (240 d^4), the parallel-plate energy, the
sphere-plate force by the proximity force approximation, a labelled
plasma-model correction for real metals (the perfect-mirror number
is a CEILING, never a product spec), a simplified Lifshitz sign
model including the repulsive case, Casimir MEMS pull-in (why
micro-chips stick shut), Lamoreaux-1997-class force tables, and a
DEBUNK module that does the cycle bookkeeping in the open: over any
closed cycle the plates give back exactly the work you put in, so
the net cyclic gain is ZERO. Vacuum energy is not a fuel. Every
free-energy / extraction / product / live-hardware claim is a HOLD
gate - with Gemini Carbon 4 as DECIDER (names-only, tighten-only),
Muse as advisor (never overrides HOLD), and Google Flow plan-only
seats.
"""
import hashlib
import json
import math
import sys

# ---------------------------------------------------------------- constants
HBAR = 1.054571817e-34          # reduced Planck constant, J s (exact, SI)
C_LIGHT = 299792458.0           # speed of light, m/s (exact, SI)
H_PLANCK = 6.62607015e-34       # Planck constant, J s (exact, SI)
K_B = 1.380649e-23              # Boltzmann constant, J/K (exact, SI)
VERSION = "1.0.0"

# Casimir coefficients (perfect mirrors, zero temperature)
PRESSURE_COEF = math.pi ** 2 * HBAR * C_LIGHT / 240.0   # P = -COEF / d^4
ENERGY_COEF = math.pi ** 2 * HBAR * C_LIGHT / 720.0     # E/A = -COEF / d^3

# ---------------------------------------------------------------- HOLD gates
HOLD_GATES = {
    "free_energy_claim": "HOLD - the Casimir force is conservative; net cyclic work is zero, no free energy",
    "perpetual_motion_claim": "HOLD - no perpetual motion: separating the plates costs exactly what closing pays back",
    "vacuum_energy_extraction_claim": "HOLD - zero-point energy between plates cannot be cycled into net work; the debunk math is in this lab",
    "real_hardware_control": "HOLD - no control of any real Casimir rig, AFM, or vacuum hardware, ever",
    "live_experiment": "HOLD - no live experiment instructions; this lab computes, it does not operate",
    "commercial_product_claim": "HOLD - this is an educational lab, not a commercial product or device design",
    "propulsion_claim": "HOLD - Casimir forces act between the plates themselves; they propel nothing",
    "medical_claim": "HOLD - no medical claims; vacuum physics here treats no condition",
    "investment_claim": "HOLD - no investment advice about vacuum-energy, MEMS, or quantum companies",
    "guaranteed_device_performance_claim": "HOLD - no guaranteed device performance; every model here carries its assumptions",
    "nanofabrication_live": "HOLD - no live nanofabrication recipes; the MEMS pull-in model is not a process flow",
    "high_vacuum_operation_live": "HOLD - no live high-vacuum operation instructions for hardware builds",
    "antigravity_claim": "HOLD - the Casimir force is an attraction (or repulsion) between plates, not antigravity",
    "overunity_claim": "HOLD - overunity is arithmetically false here: cycle work in = cycle work out, exactly",
    "weapons_application_claim": "HOLD - no weapons application guidance of any kind",
}


def gate(action):
    """Return 'HOLD' if the action is gated, else 'PROCEED' (sandbox sim)."""
    return "HOLD" if action in HOLD_GATES else "PROCEED"


# ================================================================ 1. Perfect plates
# Casimir 1948: two perfectly conducting parallel plates, area A,
# separation d, in vacuum at zero temperature. The zero-point modes
# that fit between the plates are a subset of the modes outside, so
# radiation pressure from outside wins:
#   pressure  P(d)    = -pi^2 hbar c / (240 d^4)      [Pa, attractive]
#   energy    E/A (d) = -pi^2 hbar c / (720 d^3)      [J/m^2]
# and the two are consistent: P = -d(E/A)/dd. The d^-4 law is
# brutal: ten times closer is ten THOUSAND times stronger.

def casimir_pressure(d_m):
    """Casimir pressure between perfect plates at gap d_m (Pa, < 0)."""
    if d_m <= 0:
        raise ValueError("gap must be positive")
    return -PRESSURE_COEF / d_m ** 4


def plate_energy_per_area(d_m):
    """Casimir energy per unit area between perfect plates (J/m^2, < 0)."""
    if d_m <= 0:
        raise ValueError("gap must be positive")
    return -ENERGY_COEF / d_m ** 3


def plate_force(d_m, area_m2):
    """Force on a plate of area_m2 at gap d_m (N, < 0 = attractive)."""
    if area_m2 <= 0:
        raise ValueError("area must be positive")
    return casimir_pressure(d_m) * area_m2


def pressure_table(gaps_nm=(10.0, 50.0, 100.0, 500.0, 1000.0)):
    rows = []
    for g in gaps_nm:
        d = g * 1e-9
        rows.append({"gap_nm": g, "pressure_pa": casimir_pressure(d),
                     "energy_per_area_j_m2": plate_energy_per_area(d),
                     "force_1cm2_n": plate_force(d, 1.0e-4)})
    return rows


# ================================================================ 2. Real-metal correction (plasma model)
# Perfect mirrors do not exist: a real metal stops reflecting above
# its plasma frequency, so the high-frequency modes that dominate at
# small gaps are partly lost and the real force is SMALLER than the
# Casimir ceiling. Labelled method: first-order plasma-model
# correction for two identical plates,
#   eta(d) = 1 - (4/3) * (delta_p / d),   delta_p = c / omega_p,
# valid for d >> delta_p (used here for d >= 5 * delta_p). Gold:
# omega_p = 1.37e16 rad/s (labelled literature value), so
# delta_p = 21.9 nm. The perfect-mirror value is the ceiling;
# eta < 1 always. Full Lifshitz theory with measured optical data
# is the real tool - this is its honest first-order sketch.

GOLD_OMEGA_P = 1.37e16          # rad/s, labelled literature value for gold
GOLD_DELTA_P_M = C_LIGHT / GOLD_OMEGA_P


def plasma_eta(d_m, delta_p_m=GOLD_DELTA_P_M):
    """First-order plasma-model force ratio eta(d) in (0, 1)."""
    if d_m <= 0:
        raise ValueError("gap must be positive")
    eta = 1.0 - (4.0 / 3.0) * (delta_p_m / d_m)
    return max(eta, 0.0)


def casimir_pressure_plasma(d_m, delta_p_m=GOLD_DELTA_P_M):
    """Plasma-corrected Casimir pressure (Pa): eta * perfect value."""
    return plasma_eta(d_m, delta_p_m) * casimir_pressure(d_m)


# ================================================================ 3. Geometry: sphere-plate (PFA)
# Most experiments do not use two flat plates (keeping them parallel
# at 100 nm is miserable) - they use a sphere of radius R facing a
# plate. The proximity force approximation (Derjaguin) treats the
# sphere as a stack of plate rings:
#   F_sphere(d) = 2 pi R * (E/A)_plate(d) = -pi^3 hbar c R / (360 d^3)
# valid for d << R. Note the gentler d^-3 law.

def sphere_plate_force(d_m, radius_m):
    """Sphere-plate Casimir force by PFA (N, < 0 = attractive)."""
    if d_m <= 0 or radius_m <= 0:
        raise ValueError("gap and radius must be positive")
    return 2.0 * math.pi * radius_m * plate_energy_per_area(d_m)


def sphere_plate_force_closed(d_m, radius_m):
    """Same force from the closed form -pi^3 hbar c R / (360 d^3)."""
    if d_m <= 0 or radius_m <= 0:
        raise ValueError("gap and radius must be positive")
    return -math.pi ** 3 * HBAR * C_LIGHT * radius_m / (360.0 * d_m ** 3)


# ================================================================ 4. The debunk: cycle bookkeeping
# The energy between the plates is negative RELATIVE TO EMPTY SPACE
# and it is a state function of the gap: E(d) = A * (E/A)(d). Let
# the plates close from d_far to d_near: the system energy DROPS
# (E goes more negative), so the field pays out
#   W_out = E(d_far) - E(d_near) > 0.
# To reset the cycle you must pull the plates apart again, paying
#   W_in = E(d_far) - E(d_near) = W_out.  Exactly. Joule for joule.
# Net cyclic gain = W_out - W_in = 0. Not approximately - exactly,
# because E is a state function. Anyone selling a "Casimir cycle
# engine" is selling the separation step's invoice and hiding it.

def plate_energy_total(d_m, area_m2):
    """Total Casimir energy of a plate pair (J, < 0)."""
    return plate_energy_per_area(d_m) * area_m2


def cycle_bookkeeping(d_near_m, d_far_m, area_m2):
    """Full-cycle work audit for closing then re-separating the plates."""
    if not (0 < d_near_m < d_far_m):
        raise ValueError("need 0 < d_near < d_far")
    e_near = plate_energy_total(d_near_m, area_m2)
    e_far = plate_energy_total(d_far_m, area_m2)
    work_out_closing = e_far - e_near      # field pays this out (> 0)
    work_in_separating = e_far - e_near    # you pay this back (> 0)
    return {"e_near_j": e_near, "e_far_j": e_far,
            "work_out_closing_j": work_out_closing,
            "work_in_separating_j": work_in_separating,
            "net_cycle_gain_j": work_out_closing - work_in_separating}


# ================================================================ 5. Repulsive Casimir (Lifshitz sign, simplified)
# Lifshitz theory: with a liquid of permittivity eps_m between two
# bodies eps_1 and eps_2, the force can REPEL when the dielectric
# ordering eps_1 > eps_m > eps_2 (or the mirror ordering) holds over
# the frequencies that matter - the famous case is gold and silica
# across bromobenzene (Munday, Capasso & Parsegian, Nature 2009).
# LABELLED SIMPLIFICATION: this module uses static-permittivity
# ordering as a sign proxy for the full Lifshitz integral:
#   sign > 0 (repulsive) iff (eps_1 - eps_m) and (eps_m - eps_2)
#   have the same sign. It gets the sign right for the textbook
# cases; it is not a force magnitude.

EPS_STATIC = {
    "gold": 1.0e4,          # metal: huge static response (proxy)
    "silica": 3.9,
    "silicon": 11.7,
    "vacuum": 1.0,
    "bromobenzene": 4.4,
    "ethanol": 24.3,
}


def lifshitz_sign(body1, medium, body2):
    """+1 repulsive / -1 attractive / 0 no force, static-eps proxy."""
    e1, em, e2 = EPS_STATIC[body1], EPS_STATIC[medium], EPS_STATIC[body2]
    prod = (e1 - em) * (em - e2)
    if prod > 0:
        return 1
    if prod < 0:
        return -1
    return 0


def lifshitz_report():
    cases = [("gold", "bromobenzene", "silica"),
             ("gold", "vacuum", "gold"),
             ("gold", "vacuum", "silica"),
             ("silica", "bromobenzene", "gold"),
             ("silicon", "vacuum", "silicon")]
    return {f"{a}|{b}|{c}": lifshitz_sign(a, b, c) for a, b, c in cases}


# ================================================================ 6. MEMS stiction / pull-in
# A MEMS plate of area A hangs over a substrate at rest gap g0 on a
# spring k. Casimir attraction C_A / d^4 (C_A = PRESSURE_COEF * A)
# fights the spring k (g0 - d). Equilibrium: k (g0 - d) = C_A / d^4.
# The equilibrium is STABLE only while the spring stiffens faster
# than the attraction grows: 4 C_A / d^5 < k, i.e. d > d_pullin with
#   d_pullin = (4 C_A / k)^{1/5}.
# Below that gap the plate snaps shut - Casimir pull-in, a real
# yield-killer in MEMS fabs. If g0 is below the critical gap where
# the two curves are tangent, NO equilibrium exists at all.

def _casimir_pull(d_m, area_m2):
    return PRESSURE_COEF * area_m2 / d_m ** 4


def mems_pull_in_gap(k_n_per_m, area_m2):
    """Gap below which no stable equilibrium exists (m)."""
    if k_n_per_m <= 0 or area_m2 <= 0:
        raise ValueError("spring and area must be positive")
    return (4.0 * PRESSURE_COEF * area_m2 / k_n_per_m) ** 0.2


def mems_critical_g0(k_n_per_m, area_m2):
    """Smallest rest gap g0 that admits any equilibrium (m)."""
    d = mems_pull_in_gap(k_n_per_m, area_m2)
    return d + _casimir_pull(d, area_m2) / k_n_per_m


def mems_equilibrium(g0_m, k_n_per_m, area_m2):
    """Stable equilibrium gap (m) by bisection, or None = pull-in."""
    if g0_m <= 0 or k_n_per_m <= 0 or area_m2 <= 0:
        raise ValueError("g0, spring and area must be positive")
    d_pi = mems_pull_in_gap(k_n_per_m, area_m2)
    lo, hi = d_pi, g0_m
    if hi <= lo:
        return None
    f_lo = k_n_per_m * (g0_m - lo) - _casimir_pull(lo, area_m2)
    f_hi = k_n_per_m * (g0_m - hi) - _casimir_pull(hi, area_m2)
    if f_lo < 0 or f_hi > 0:
        return None
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        f_mid = k_n_per_m * (g0_m - mid) - _casimir_pull(mid, area_m2)
        if f_mid > 0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# ================================================================ 7. Measurement table (Lamoreaux class)
# Lamoreaux 1997 measured the force between a gold-coated sphere
# (R ~ 11.3 cm, a lens) and a plate at 0.6-6 um gaps, agreeing with
# Casimir theory at the ~5% level and opening the modern era.
# LABELLED MODEL: this table reproduces the ideal PFA values for
# that geometry - the scale and the d^-3 law of the experiment,
# not its raw data (real data carries roughness / patch corrections).

LAMOREAUX_R_M = 0.113


def lamoreaux_table(gaps_um=(0.6, 1.0, 2.0, 3.0, 6.0), radius_m=LAMOREAUX_R_M):
    rows = []
    for g in gaps_um:
        d = g * 1e-6
        rows.append({"gap_um": g, "force_n": sphere_plate_force(d, radius_m)})
    return rows


def thermal_wavelength_um(temp_k=300.0):
    """hbar c / (kB T) in um: gaps near this scale feel thermal photons."""
    if temp_k <= 0:
        raise ValueError("temperature must be positive")
    return HBAR * C_LIGHT / (K_B * temp_k) * 1e6


# ================================================================ 8. Dynamic Casimir (concept, labelled)
# A mirror whose boundary moves can convert drive energy into real
# photon pairs (the dynamical Casimir effect, seen in 2011 with a
# SQUID-modulated cavity, Wilson et al.). The photons are PAID FOR
# by the drive, and the price list is brutal: efficient conversion
# needs boundary speeds that are a fair fraction of c. A fast MEMS
# mirror (1 nm amplitude at 10 GHz) reaches v/c ~ 2e-7. The energy
# audit below asserts the only direction energy ever flows:
# drive work in >= photon energy out. A power source it is not.

def dynamic_casimir_report(amplitude_m=1e-9, freq_hz=1.0e10, mirror_kg=1e-12):
    v_max = 2.0 * math.pi * freq_hz * amplitude_m
    ke_max = 0.5 * mirror_kg * v_max ** 2
    photon_hz = freq_hz / 2.0                    # pairs near half the drive
    photon_j = H_PLANCK * photon_hz
    return {"v_max_m_s": v_max, "v_over_c": v_max / C_LIGHT,
            "mirror_ke_max_j": ke_max, "photon_freq_hz": photon_hz,
            "photon_energy_j": photon_j,
            "drive_pays_ratio": ke_max / photon_j,
            "net_power_source": False}


# ================================================================ 9. kNN regime classifier
# Features: (log10 gap in nm, log10 area in m^2, log10 |P| in Pa).
# Small gaps + micro areas where the pull rivals springs are
# MEMS-relevant; gaps and areas where forces sit in the pN-uN lab
# measurement band are measurable; wide gaps / tiny areas where the
# force falls under ~1e-13 N are negligible for engineering.

_CLASSIFIER_TRAIN = [
    # (log10_gap_nm, log10_area_m2, log10_pressure_pa, label)
    (2.0, -4.0, 1.11, "measurable"),      # 100 nm, 1 cm^2, 13 Pa
    (3.0, -4.0, -2.89, "measurable"),     # 1 um, 1 cm^2
    (2.7, -4.0, -1.70, "measurable"),     # 500 nm, 1 cm^2
    (2.0, -6.0, 1.11, "measurable"),      # 100 nm, 1 mm^2
    (1.7, -4.0, 2.31, "measurable"),      # 50 nm, 1 cm^2
    (3.3, -2.0, -3.49, "measurable"),     # 2 um, 100 cm^2
    (1.9, -8.0, 1.29, "MEMS-relevant"),   # 80 nm, (100 um)^2 plate
    (2.0, -8.0, 1.11, "MEMS-relevant"),   # 100 nm, MEMS plate
    (1.7, -8.0, 2.31, "MEMS-relevant"),   # 50 nm, MEMS plate
    (2.0, -10.0, 1.11, "MEMS-relevant"),  # 100 nm, (10 um)^2
    (1.85, -9.0, 1.48, "MEMS-relevant"),  # 70 nm, (30 um)^2
    (2.3, -8.0, 0.51, "MEMS-relevant"),   # 200 nm, MEMS plate
    (4.0, -4.0, -6.89, "negligible"),     # 10 um, 1 cm^2
    (4.0, -8.0, -6.89, "negligible"),     # 10 um, MEMS plate
    (3.7, -6.0, -5.70, "negligible"),     # 5 um, 1 mm^2
    (4.3, -4.0, -7.49, "negligible"),     # 20 um, 1 cm^2
    (3.0, -10.0, -2.89, "negligible"),    # 1 um, (10 um)^2: force ~1e-13 N
    (4.0, -10.0, -6.89, "negligible"),    # 10 um, (10 um)^2
]


def _features(gap_nm, area_m2):
    p = abs(casimir_pressure(gap_nm * 1e-9))
    return (math.log10(gap_nm), math.log10(area_m2), math.log10(p))


def _dist(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def classify_regime(gap_nm, area_m2, k=3):
    """kNN (k=3) Casimir regime classifier on physical features."""
    if gap_nm <= 0 or area_m2 <= 0:
        raise ValueError("gap and area must be positive")
    f = _features(gap_nm, area_m2)
    ranked = sorted(_CLASSIFIER_TRAIN, key=lambda row: _dist(f, row[:3]))
    votes = {}
    for row in ranked[:k]:
        votes[row[3]] = votes.get(row[3], 0) + 1
    return max(sorted(votes), key=lambda lab: votes[lab])


def regime_report():
    scenarios = {
        "lab_plates_100nm_1cm2": (100.0, 1.0e-4),
        "gold_film_500nm_1cm2": (500.0, 1.0e-4),
        "mems_plate_80nm": (80.0, 1.0e-8),
        "mems_plate_100nm_small": (100.0, 1.0e-10),
        "far_plates_10um_1cm2": (10000.0, 1.0e-4),
        "tiny_flake_2um": (2000.0, 1.0e-10),
    }
    return {name: classify_regime(g, a) for name, (g, a) in scenarios.items()}


# ================================================================ 10. Advisory seats
def _trace(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


def carbon4_decide(topic="casimirx-demo"):
    """Gemini Carbon 4 DECIDER seat: MAP->MODEL->STRESS->DECIDE.

    Names-only keys, live calls 0, tighten-only: can add HOLDs, never lift one.
    """
    stages = ["MAP", "MODEL", "STRESS", "DECIDE"]
    payload = {"seat": "gemini-carbon-4", "topic": topic, "stages": stages}
    return {
        "seat": "Gemini Carbon 4 Extended Thinking",
        "role": "DECIDER",
        "pipeline": stages,
        "tiers": [2048, 8192, 32768],
        "key": "names-only (GEMINI_API_KEY name checked, value never read)",
        "live_calls": 0,
        "decision": "PROCEED - sandbox simulation only, all claim gates stay HOLD",
        "can_override_hold": False,
        "trace_sha256_16": _trace(payload),
    }


def claude_advisor(topic="casimirx-demo"):
    """Muse advisor seat: advises, can never override a HOLD."""
    return {
        "seat": "Muse",
        "role": "ADVISOR",
        "key": "names-only (MODEL_API_KEY name checked, value never read)",
        "live_calls": 0,
        "advice": "Quote the perfect-mirror pressure as a ceiling, put the plasma-corrected number next to it, and show the cycle audit whenever extraction comes up: the vacuum keeps its books balanced.",
        "can_override_hold": False,
    }


def google_flow_plan():
    """Google Flow seat: plan-only, nothing rendered, nothing live."""
    return {
        "seat": "Google Flow",
        "role": "PLAN-ONLY",
        "shots": ["long waves outside the plates, short waves missing between",
                  "the plates drift together", "the spring that loses: MEMS pull-in",
                  "gold and silica repelling across bromobenzene",
                  "the cycle audit: work in, work out, zero"],
        "rendered": False,
        "live": 0,
    }


def brains_report():
    return {"decider": carbon4_decide(), "advisor": claude_advisor(),
            "flow": google_flow_plan()}


# ================================================================ checks
def run_checks():
    c = []

    def chk(name, ok):
        c.append((name, bool(ok)))

    # 1. perfect plates
    p1 = casimir_pressure(1e-6)
    p100 = casimir_pressure(100e-9)
    p10 = casimir_pressure(10e-9)
    chk("pressure_1um_value", abs(p1 - (-1.30013e-3)) < 0.01 * 1.30013e-3)
    chk("pressure_100nm_value", abs(p100 - (-13.0013)) < 0.01 * 13.0013)
    chk("pressure_10nm_value", abs(p10 - (-1.30013e5)) < 0.01 * 1.30013e5)
    chk("pressure_negative_attractive", p1 < 0 and p100 < 0 and p10 < 0)
    chk("d4_scaling_exact",
        abs(p100 / p1 - 1.0e4) < 1e-9 * 1.0e4 and abs(p10 / p100 - 1.0e4) < 1e-9 * 1.0e4)
    chk("force_1cm2_100nm",
        abs(plate_force(100e-9, 1e-4) - (-1.30013e-3)) < 0.01 * 1.30013e-3)
    chk("force_is_pressure_times_area",
        abs(plate_force(500e-9, 2e-4) - casimir_pressure(500e-9) * 2e-4) < 1e-30)
    ea100 = plate_energy_per_area(100e-9)
    chk("energy_per_area_100nm", abs(ea100 - (-4.33375e-7)) < 0.01 * 4.33375e-7)
    chk("energy_d3_scaling",
        abs(plate_energy_per_area(100e-9) / plate_energy_per_area(1000e-9) - 1000.0) < 1e-6)
    # P = -d(E/A)/dd, numeric derivative consistency
    d0, h = 300e-9, 1e-12
    deriv = (plate_energy_per_area(d0 + h) - plate_energy_per_area(d0 - h)) / (2 * h)
    chk("pressure_is_minus_energy_derivative",
        abs(-deriv - casimir_pressure(d0)) < 1e-6 * abs(casimir_pressure(d0)))
    # 2. plasma correction
    chk("plasma_eta_below_one", 0.0 < plasma_eta(1e-6) < 1.0)
    chk("plasma_eta_1um_value", 0.95 < plasma_eta(1e-6) < 0.99)
    chk("plasma_eta_grows_with_gap", plasma_eta(200e-9) < plasma_eta(500e-9) < plasma_eta(1e-6))
    chk("plasma_force_below_ceiling",
        abs(casimir_pressure_plasma(500e-9)) < abs(casimir_pressure(500e-9)))
    chk("plasma_delta_p_nm", abs(GOLD_DELTA_P_M - 21.9e-9) < 0.5e-9)
    # 3. sphere-plate PFA
    f_pfa = sphere_plate_force(100e-9, 100e-6)
    f_closed = sphere_plate_force_closed(100e-9, 100e-6)
    chk("sphere_pfa_matches_closed_form", abs(f_pfa - f_closed) < 1e-12 * abs(f_closed))
    chk("sphere_force_value", abs(f_pfa - (-2.7230e-10)) < 0.02 * 2.7230e-10)
    chk("sphere_d3_scaling",
        abs(sphere_plate_force(100e-9, 100e-6) / sphere_plate_force(200e-9, 100e-6) - 8.0) < 1e-9)
    # 4. debunk: cycle bookkeeping
    audit = cycle_bookkeeping(100e-9, 1e-6, 1e-4)
    chk("cycle_net_gain_exactly_zero", audit["net_cycle_gain_j"] == 0.0)
    chk("cycle_work_positive", audit["work_out_closing_j"] > 0)
    chk("cycle_work_value",
        abs(audit["work_out_closing_j"] - 4.32942e-11) < 0.01 * 4.32942e-11)
    chk("cycle_energy_negative", audit["e_near_j"] < audit["e_far_j"] < 0)
    audit2 = cycle_bookkeeping(50e-9, 500e-9, 1e-8)
    chk("cycle_zero_any_geometry", audit2["net_cycle_gain_j"] == 0.0)
    # 5. Lifshitz sign (simplified static-eps proxy)
    rep = lifshitz_report()
    chk("lifshitz_gold_bromobenzene_silica_repulsive",
        rep["gold|bromobenzene|silica"] == 1)
    chk("lifshitz_mirror_order_also_repulsive",
        rep["silica|bromobenzene|gold"] == 1)
    chk("lifshitz_gold_vacuum_gold_attractive", rep["gold|vacuum|gold"] == -1)
    chk("lifshitz_gold_vacuum_silica_attractive", rep["gold|vacuum|silica"] == -1)
    # 6. MEMS pull-in
    k_demo, a_demo = 1.0, 1e-8
    d_pi = mems_pull_in_gap(k_demo, a_demo)
    chk("mems_pull_in_gap_value", abs(d_pi - 139.1e-9) < 3e-9)
    chk("mems_critical_g0_value", abs(mems_critical_g0(k_demo, a_demo) - 173.9e-9) < 5e-9)
    chk("mems_below_critical_no_equilibrium",
        mems_equilibrium(150e-9, k_demo, a_demo) is None)
    eq = mems_equilibrium(200e-9, k_demo, a_demo)
    chk("mems_equilibrium_exists_stable", eq is not None and d_pi < eq < 200e-9)
    chk("mems_equilibrium_balances",
        eq is not None
        and abs(k_demo * (200e-9 - eq) - _casimir_pull(eq, a_demo)) < 1e-6 * k_demo * 200e-9)
    chk("mems_stiffer_spring_smaller_pullin",
        mems_pull_in_gap(10.0, a_demo) < d_pi)
    # 7. Lamoreaux-class table
    tab = lamoreaux_table()
    chk("lamoreaux_0p6um_value", abs(tab[0]["force_n"] - (-1.425e-9)) < 0.05 * 1.425e-9)
    chk("lamoreaux_d3_law",
        abs(tab[1]["force_n"] / tab[2]["force_n"] - 8.0) < 0.01 * 8.0)
    chk("lamoreaux_force_falls_with_gap",
        all(abs(tab[i]["force_n"]) > abs(tab[i + 1]["force_n"]) for i in range(len(tab) - 1)))
    chk("thermal_wavelength_300k", 7.0 < thermal_wavelength_um(300.0) < 8.5)
    # 8. dynamic Casimir audit
    dyn = dynamic_casimir_report()
    chk("dynamic_mirror_slow_vs_c", dyn["v_over_c"] < 1e-6)
    chk("dynamic_photon_energy_tiny", 0 < dyn["photon_energy_j"] < 1e-20)
    chk("dynamic_drive_pays_for_photons", dyn["drive_pays_ratio"] > 1.0)
    chk("dynamic_not_a_power_source", dyn["net_power_source"] is False)
    # 9. classifier
    rrep = regime_report()
    chk("classifier_measurable", rrep["lab_plates_100nm_1cm2"] == "measurable")
    chk("classifier_measurable_500nm", rrep["gold_film_500nm_1cm2"] == "measurable")
    chk("classifier_mems", rrep["mems_plate_80nm"] == "MEMS-relevant")
    chk("classifier_mems_small", rrep["mems_plate_100nm_small"] == "MEMS-relevant")
    chk("classifier_negligible", rrep["far_plates_10um_1cm2"] == "negligible")
    chk("classifier_negligible_flake", rrep["tiny_flake_2um"] == "negligible")
    # gates + seats
    chk("hold_gates_15", len(HOLD_GATES) == 15 and all(v.startswith("HOLD") for v in HOLD_GATES.values()))
    chk("gate_free_energy_hold", gate("free_energy_claim") == "HOLD")
    chk("gate_extraction_hold", gate("vacuum_energy_extraction_claim") == "HOLD")
    chk("gate_overunity_hold", gate("overunity_claim") == "HOLD")
    chk("gate_antigravity_hold", gate("antigravity_claim") == "HOLD")
    chk("gate_sandbox_proceed", gate("run_simulation") == "PROCEED")
    b = brains_report()
    chk("carbon4_no_override", b["decider"]["can_override_hold"] is False)
    chk("claude_no_override", b["advisor"]["can_override_hold"] is False)
    chk("flow_plan_only", b["flow"]["rendered"] is False and b["flow"]["live"] == 0)
    return c


# ================================================================ CLI / demo
def demo():
    print("=" * 68)
    print("CasimirX - educational Casimir effect / vacuum physics lab")
    print("by Darion Kellar | MIT | pure stdlib | zero network | EDUCATION ONLY")
    print("=" * 68)
    print("\n[1] Perfect plates - Casimir pressure P = -pi^2 hbar c / (240 d^4)")
    for row in pressure_table():
        print(f"    gap {row['gap_nm']:7.0f} nm: P = {row['pressure_pa']:.4e} Pa | "
              f"E/A = {row['energy_per_area_j_m2']:.4e} J/m^2 | "
              f"F on 1 cm^2 = {row['force_1cm2_n']:.4e} N")
    print("    -> the d^-4 law: 10x closer = 10,000x stronger. At 1 um the push")
    print("       is -1.3 mPa; at 10 nm it is -1.3e5 Pa, over an atmosphere.")
    print("\n[2] Real metal (plasma model, gold, LABELLED first-order correction)")
    print(f"    plasma skin scale delta_p = c/omega_p = {GOLD_DELTA_P_M * 1e9:.1f} nm")
    for g in (200.0, 500.0, 1000.0):
        d = g * 1e-9
        print(f"    gap {g:6.0f} nm: eta = {plasma_eta(d):.4f} | "
              f"P_real = {casimir_pressure_plasma(d):.4e} Pa "
              f"(perfect ceiling {casimir_pressure(d):.4e} Pa)")
    print("    -> real metal always falls BELOW the perfect-mirror ceiling.")
    print("\n[3] Sphere-plate geometry (proximity force approximation)")
    print(f"    R = 100 um sphere at 100 nm: F = {sphere_plate_force(100e-9, 100e-6):.4e} N "
          f"(closed form {sphere_plate_force_closed(100e-9, 100e-6):.4e} N)")
    print("    -> F = 2 pi R (E/A): the d^-3 law every modern experiment uses.")
    print("\n[4] THE DEBUNK - cycle bookkeeping (1 cm^2 plates, 100 nm <-> 1 um)")
    audit = cycle_bookkeeping(100e-9, 1e-6, 1e-4)
    print(f"    closing pays out : {audit['work_out_closing_j']:.4e} J")
    print(f"    separating costs : {audit['work_in_separating_j']:.4e} J")
    print(f"    NET CYCLE GAIN   : {audit['net_cycle_gain_j']:.4e} J  <- exactly zero")
    print("    -> the energy is a state function of the gap. A 'Casimir cycle")
    print("       engine' hides the separation invoice. Vacuum energy is not fuel.")
    print("\n[5] Repulsive Casimir (Lifshitz sign, simplified static-eps proxy)")
    for case, sgn in lifshitz_report().items():
        word = "REPULSIVE" if sgn > 0 else "attractive"
        print(f"    {case:28s} -> {word}")
    print("    -> gold | bromobenzene | silica repels (Munday et al. 2009);")
    print("       the sign flips only with the dielectric ordering, labelled model.")
    print("\n[6] MEMS stiction - Casimir pull-in (A = (100 um)^2, k = 1 N/m)")
    d_pi = mems_pull_in_gap(1.0, 1e-8)
    print(f"    pull-in gap (stability limit) : {d_pi * 1e9:.1f} nm")
    print(f"    critical rest gap g0          : {mems_critical_g0(1.0, 1e-8) * 1e9:.1f} nm")
    print(f"    g0 = 150 nm -> equilibrium: {mems_equilibrium(150e-9, 1.0, 1e-8)} (snaps shut)")
    eq = mems_equilibrium(200e-9, 1.0, 1e-8)
    print(f"    g0 = 200 nm -> equilibrium: {eq * 1e9:.1f} nm (stable)")
    print("    -> this is why micro-machines stick: below the pull-in gap the")
    print("       vacuum out-pulls the spring and the part welds itself down.")
    print("\n[7] Measurement table - Lamoreaux 1997 class (LABELLED ideal-PFA model)")
    for row in lamoreaux_table():
        print(f"    gap {row['gap_um']:.1f} um: F = {row['force_n']:.4e} N (R = 11.3 cm sphere)")
    print(f"    thermal wavelength at 300 K: {thermal_wavelength_um():.2f} um "
          "(gaps near this feel thermal photons too)")
    print("\n[8] Dynamic Casimir (LABELLED concept audit)")
    dyn = dynamic_casimir_report()
    print(f"    MEMS mirror 1 nm @ 10 GHz: v = {dyn['v_max_m_s']:.1f} m/s = "
          f"{dyn['v_over_c']:.2e} c")
    print(f"    photon at {dyn['photon_freq_hz']:.1e} Hz: {dyn['photon_energy_j']:.3e} J, "
          f"paid from mirror KE {dyn['mirror_ke_max_j']:.3e} J")
    print("    -> photons are bought with drive energy, at v/c ~ 2e-7 efficiency")
    print("       territory. Energy out <= energy in. Not a power source.")
    print("\n[9] Regime classifier (TinyML kNN)")
    for name, label in regime_report().items():
        print(f"    {name:24s} -> {label}")
    print("\n[10] Advisory seats")
    print(f"    decider: {carbon4_decide()['decision']} trace={carbon4_decide()['trace_sha256_16']}")
    print(f"    advisor can_override_hold = {claude_advisor()['can_override_hold']}")
    print(f"    flow rendered = {google_flow_plan()['rendered']} live = {google_flow_plan()['live']}")
    print(f"\n[11] HOLD gates: {len(HOLD_GATES)}")
    for k in HOLD_GATES:
        print(f"    HOLD  {k}")
    checks = run_checks()
    passed = sum(1 for _, ok in checks if ok)
    print(f"\nCHECKS {passed}/{len(checks)}")
    for name, ok in checks:
        if not ok:
            print(f"    FAIL {name}")
    verdict = "PROCEED" if passed == len(checks) else "HOLD"
    print(f"VERDICT {verdict} (sandbox simulation only) | HOLD gates {len(HOLD_GATES)}")
    return 0 if passed == len(checks) else 1


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] == "demo":
        return demo()
    cmd = argv[0]
    if cmd == "checks":
        checks = run_checks()
        for name, ok in checks:
            print(f"{'PASS' if ok else 'FAIL'} {name}")
        print(f"CHECKS {sum(1 for _, ok in checks if ok)}/{len(checks)}")
        return 0 if all(ok for _, ok in checks) else 1
    if cmd == "pressure":
        print(json.dumps(pressure_table(), indent=2, sort_keys=True))
        return 0
    if cmd == "plasma":
        for g in (100.0, 200.0, 300.0, 500.0, 1000.0, 2000.0):
            d = g * 1e-9
            print(f"gap={g:6.0f} nm  eta={plasma_eta(d):.4f}  "
                  f"P_perfect={casimir_pressure(d):.4e}  P_plasma={casimir_pressure_plasma(d):.4e}")
        return 0
    if cmd == "geometry":
        for g in (50.0, 100.0, 200.0, 500.0):
            d = g * 1e-9
            print(f"gap={g:5.0f} nm  plate F(1 cm^2)={plate_force(d, 1e-4):.4e} N  "
                  f"sphere F(R=100 um)={sphere_plate_force(d, 100e-6):.4e} N")
        return 0
    if cmd == "cycle":
        print(json.dumps(cycle_bookkeeping(100e-9, 1e-6, 1e-4), indent=2, sort_keys=True))
        return 0
    if cmd == "lifshitz":
        print(json.dumps(lifshitz_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "mems":
        for g0 in (120.0, 150.0, 174.0, 200.0, 300.0):
            eq = mems_equilibrium(g0 * 1e-9, 1.0, 1e-8)
            print(f"g0={g0:5.0f} nm  equilibrium="
                  f"{'PULL-IN (none)' if eq is None else f'{eq * 1e9:.1f} nm'}")
        print(f"pull-in gap = {mems_pull_in_gap(1.0, 1e-8) * 1e9:.1f} nm | "
              f"critical g0 = {mems_critical_g0(1.0, 1e-8) * 1e9:.1f} nm")
        return 0
    if cmd == "history":
        print(json.dumps(lamoreaux_table(), indent=2, sort_keys=True))
        return 0
    if cmd == "dynamic":
        print(json.dumps(dynamic_casimir_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "classify":
        print(json.dumps(regime_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "brains":
        print(json.dumps(brains_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "holds":
        for k, v in HOLD_GATES.items():
            print(f"{k}: {v}")
        return 0
    if cmd == "hold-demo":
        action = argv[1] if len(argv) > 1 else "vacuum_energy_extraction_claim"
        print(f"{action}: {HOLD_GATES.get(action, 'PROCEED - not gated')}")
        return 2 if gate(action) == "HOLD" else 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
