"""Tests for CasimirX: every number checked against analytics."""
import math

import pytest

import main as m


# ---- perfect plates (Casimir 1948 closed form)
def test_pressure_1um_value():
    assert abs(m.casimir_pressure(1e-6) - (-1.30013e-3)) < 0.01 * 1.30013e-3


def test_pressure_100nm_value():
    assert abs(m.casimir_pressure(100e-9) - (-13.0013)) < 0.01 * 13.0013


def test_pressure_10nm_value():
    assert abs(m.casimir_pressure(10e-9) - (-1.30013e5)) < 0.01 * 1.30013e5


def test_pressure_always_attractive():
    for d in (10e-9, 100e-9, 1e-6, 10e-6):
        assert m.casimir_pressure(d) < 0


def test_d4_scaling_exact():
    assert abs(m.casimir_pressure(100e-9) / m.casimir_pressure(1e-6) - 1e4) < 1e-5
    assert abs(m.casimir_pressure(10e-9) / m.casimir_pressure(100e-9) - 1e4) < 1e-5


def test_force_1cm2_at_100nm():
    assert abs(m.plate_force(100e-9, 1e-4) - (-1.30013e-3)) < 0.01 * 1.30013e-3


def test_energy_per_area_100nm():
    assert abs(m.plate_energy_per_area(100e-9) - (-4.33375e-7)) < 0.01 * 4.33375e-7


def test_energy_d3_scaling():
    ratio = m.plate_energy_per_area(100e-9) / m.plate_energy_per_area(1000e-9)
    assert abs(ratio - 1000.0) < 1e-6


def test_pressure_is_minus_energy_derivative():
    d0, h = 300e-9, 1e-12
    deriv = (m.plate_energy_per_area(d0 + h)
             - m.plate_energy_per_area(d0 - h)) / (2 * h)
    assert abs(-deriv - m.casimir_pressure(d0)) < 1e-6 * abs(m.casimir_pressure(d0))


def test_invalid_gap_raises():
    with pytest.raises(ValueError):
        m.casimir_pressure(0.0)
    with pytest.raises(ValueError):
        m.plate_force(100e-9, 0.0)


# ---- plasma-model correction (labelled first order)
def test_plasma_eta_below_one():
    assert 0.0 < m.plasma_eta(1e-6) < 1.0


def test_plasma_eta_1um_band():
    assert 0.95 < m.plasma_eta(1e-6) < 0.99


def test_plasma_eta_grows_with_gap():
    assert m.plasma_eta(200e-9) < m.plasma_eta(500e-9) < m.plasma_eta(1e-6)


def test_plasma_force_below_ceiling():
    assert abs(m.casimir_pressure_plasma(500e-9)) < abs(m.casimir_pressure(500e-9))


def test_gold_delta_p():
    assert abs(m.GOLD_DELTA_P_M - 21.9e-9) < 0.5e-9


# ---- sphere-plate PFA
def test_sphere_pfa_matches_closed_form():
    f1 = m.sphere_plate_force(100e-9, 100e-6)
    f2 = m.sphere_plate_force_closed(100e-9, 100e-6)
    assert abs(f1 - f2) < 1e-12 * abs(f2)


def test_sphere_force_value():
    assert abs(m.sphere_plate_force(100e-9, 100e-6) - (-2.7230e-10)) < 0.02 * 2.7230e-10


def test_sphere_d3_scaling():
    ratio = m.sphere_plate_force(100e-9, 100e-6) / m.sphere_plate_force(200e-9, 100e-6)
    assert abs(ratio - 8.0) < 1e-9


# ---- the debunk: cycle bookkeeping
def test_cycle_net_gain_exactly_zero():
    audit = m.cycle_bookkeeping(100e-9, 1e-6, 1e-4)
    assert audit["net_cycle_gain_j"] == 0.0


def test_cycle_work_value():
    audit = m.cycle_bookkeeping(100e-9, 1e-6, 1e-4)
    assert abs(audit["work_out_closing_j"] - 4.32942e-11) < 0.01 * 4.32942e-11
    assert audit["work_out_closing_j"] == audit["work_in_separating_j"]


def test_cycle_zero_any_geometry():
    assert m.cycle_bookkeeping(50e-9, 500e-9, 1e-8)["net_cycle_gain_j"] == 0.0
    assert m.cycle_bookkeeping(200e-9, 5e-6, 1e-2)["net_cycle_gain_j"] == 0.0


def test_cycle_reversed_gaps_raise():
    with pytest.raises(ValueError):
        m.cycle_bookkeeping(1e-6, 100e-9, 1e-4)


# ---- Lifshitz sign (simplified static-eps proxy)
def test_lifshitz_repulsive_case():
    assert m.lifshitz_sign("gold", "bromobenzene", "silica") == 1


def test_lifshitz_mirror_order_repulsive():
    assert m.lifshitz_sign("silica", "bromobenzene", "gold") == 1


def test_lifshitz_attractive_cases():
    assert m.lifshitz_sign("gold", "vacuum", "gold") == -1
    assert m.lifshitz_sign("gold", "vacuum", "silica") == -1
    assert m.lifshitz_sign("silicon", "vacuum", "silicon") == -1


# ---- MEMS pull-in
def test_mems_pull_in_gap_value():
    assert abs(m.mems_pull_in_gap(1.0, 1e-8) - 139.1e-9) < 3e-9


def test_mems_critical_g0_value():
    assert abs(m.mems_critical_g0(1.0, 1e-8) - 173.9e-9) < 5e-9


def test_mems_below_critical_snaps_shut():
    assert m.mems_equilibrium(150e-9, 1.0, 1e-8) is None


def test_mems_equilibrium_stable_and_balanced():
    eq = m.mems_equilibrium(200e-9, 1.0, 1e-8)
    assert eq is not None
    assert m.mems_pull_in_gap(1.0, 1e-8) < eq < 200e-9
    spring = 1.0 * (200e-9 - eq)
    pull = m.PRESSURE_COEF * 1e-8 / eq ** 4
    assert abs(spring - pull) < 1e-6 * 200e-9


def test_mems_stiffer_spring_smaller_pullin_gap():
    assert m.mems_pull_in_gap(10.0, 1e-8) < m.mems_pull_in_gap(1.0, 1e-8)


# ---- Lamoreaux-class table + thermal scale
def test_lamoreaux_first_value():
    tab = m.lamoreaux_table()
    assert abs(tab[0]["force_n"] - (-1.425e-9)) < 0.05 * 1.425e-9


def test_lamoreaux_d3_law():
    tab = m.lamoreaux_table()
    assert abs(tab[1]["force_n"] / tab[2]["force_n"] - 8.0) < 0.08


def test_lamoreaux_force_falls_with_gap():
    tab = m.lamoreaux_table()
    mags = [abs(r["force_n"]) for r in tab]
    assert all(mags[i] > mags[i + 1] for i in range(len(mags) - 1))


def test_thermal_wavelength_300k():
    assert 7.0 < m.thermal_wavelength_um(300.0) < 8.5


# ---- dynamic Casimir audit
def test_dynamic_mirror_slow_vs_c():
    assert m.dynamic_casimir_report()["v_over_c"] < 1e-6


def test_dynamic_photons_paid_by_drive():
    dyn = m.dynamic_casimir_report()
    assert 0 < dyn["photon_energy_j"] < 1e-20
    assert dyn["drive_pays_ratio"] > 1.0
    assert dyn["net_power_source"] is False


# ---- classifier
def test_classifier_scenarios():
    rep = m.regime_report()
    assert rep["lab_plates_100nm_1cm2"] == "measurable"
    assert rep["gold_film_500nm_1cm2"] == "measurable"
    assert rep["mems_plate_80nm"] == "MEMS-relevant"
    assert rep["mems_plate_100nm_small"] == "MEMS-relevant"
    assert rep["far_plates_10um_1cm2"] == "negligible"
    assert rep["tiny_flake_2um"] == "negligible"


# ---- gates + seats
def test_hold_gates_all_present():
    assert len(m.HOLD_GATES) == 15
    assert all(v.startswith("HOLD") for v in m.HOLD_GATES.values())


def test_claim_gates_hold():
    for action in ("free_energy_claim", "perpetual_motion_claim",
                   "vacuum_energy_extraction_claim", "overunity_claim",
                   "antigravity_claim", "propulsion_claim"):
        assert m.gate(action) == "HOLD"


def test_sandbox_proceeds():
    assert m.gate("run_simulation") == "PROCEED"


def test_seats_never_override():
    b = m.brains_report()
    assert b["decider"]["can_override_hold"] is False
    assert b["advisor"]["can_override_hold"] is False
    assert b["flow"]["rendered"] is False and b["flow"]["live"] == 0


def test_demo_checks_all_pass():
    checks = m.run_checks()
    assert all(ok for _, ok in checks), [n for n, ok in checks if not ok]


def test_demo_deterministic():
    import io
    import contextlib
    out1, out2 = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out1):
        m.demo()
    with contextlib.redirect_stdout(out2):
        m.demo()
    assert out1.getvalue() == out2.getvalue()
