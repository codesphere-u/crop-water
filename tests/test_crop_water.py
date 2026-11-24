"""Tests for FAO-56 Penman-Monteith ET0 physics, soil-water bucket balance, solar pump kWh & CLI."""

from __future__ import annotations

import json

import pytest

from crop_water import CropSoilProfile, DailyWeather, penman_monteith_et0, schedule_irrigation
from crop_water.cli import main as cli_main


def test_fao56_penman_monteith_matches_realistic_tropical_et0_bounds() -> None:
    # Typical warm sunny East African plateau day -> ~4.5 to 6.5 mm/day ET0
    w = DailyWeather(1, t_min_c=16.0, t_max_c=29.0, rh_mean_pct=55.0, wind_2m_ms=2.0, net_radiation_mj_m2_day=15.0)
    et0 = penman_monteith_et0(w)
    assert 4.0 <= et0 <= 6.8

    # Higher humidity & lower radiation lowers ET0 strictly
    humid = DailyWeather(2, t_min_c=16.0, t_max_c=24.0, rh_mean_pct=88.0, wind_2m_ms=1.0, net_radiation_mj_m2_day=8.0)
    assert penman_monteith_et0(humid) < et0


def test_dry_spell_triggers_irrigation_while_wet_week_skips_pumping() -> None:
    profile = CropSoilProfile(
        "Maize",
        kc=1.15,
        root_depth_m=0.8,
        field_capacity_mm_per_m=280.0,
        wilting_point_mm_per_m=130.0,
    )
    dry_days = [
        DailyWeather(d, 17.0, 30.0, 50.0, 2.2, 16.0, rainfall_mm=0.0)
        for d in range(1, 15)
    ]
    dry_rep = schedule_irrigation(dry_days, profile, area_hectares=1.0)
    assert dry_rep.irrigation_events >= 1
    assert dry_rep.total_irrigation_m3 > 0.0
    assert dry_rep.total_pump_energy_kwh > 0.0

    wet_days = [
        DailyWeather(d, 17.0, 25.0, 80.0, 1.5, 10.0, rainfall_mm=12.0)
        for d in range(1, 15)
    ]
    wet_rep = schedule_irrigation(wet_days, profile, area_hectares=1.0)
    assert wet_rep.irrigation_events == 0
    assert wet_rep.total_pump_energy_kwh == 0.0


def test_cli_demo(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli_main(["demo"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["days"] == 14
    assert out["irrigation_events"] >= 1
