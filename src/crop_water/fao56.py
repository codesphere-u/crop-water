"""FAO-56 Penman-Monteith ET0, root-zone soil-water bucket balance & solar-pump irrigation scheduler."""

from __future__ import annotations

import math
from dataclasses import dataclass

# Water density (kg/m3) * gravity (m/s2) / 3.6e6 J/kWh -> kWh per (m3 * meter head) at 100% eff
_HYDRAULIC_KWH_PER_M3_M = 9.81 / 3600.0


@dataclass(frozen=True)
class DailyWeather:
    day_index: int
    t_min_c: float
    t_max_c: float
    rh_mean_pct: float  # Mean relative humidity (0..100)
    wind_2m_ms: float  # Wind speed at 2m height (m/s)
    net_radiation_mj_m2_day: float  # Rn (MJ / m^2 / day)
    rainfall_mm: float = 0.0
    elevation_m: float = 1150.0  # Default East African plateau elevation (m)


@dataclass(frozen=True)
class CropSoilProfile:
    crop_name: str
    kc: float  # FAO-56 crop coefficient (e.g. maize mid-season = 1.20, tomatoes = 1.15)
    root_depth_m: float  # Effective rooting depth (m)
    field_capacity_mm_per_m: float  # e.g. loam ~280 mm/m
    wilting_point_mm_per_m: float  # e.g. loam ~130 mm/m
    depletion_fraction_p: float = 0.50  # Readily available water (RAW) fraction before stress

    @property
    def taw_mm(self) -> float:
        """Total Available Water (TAW) in the root zone (mm)."""
        return max(1.0, (self.field_capacity_mm_per_m - self.wilting_point_mm_per_m) * self.root_depth_m)

    @property
    def raw_mm(self) -> float:
        """Readily Available Water (RAW = p * TAW) threshold triggering irrigation (mm)."""
        return self.taw_mm * self.depletion_fraction_p


@dataclass(frozen=True)
class DailyIrrigationDecision:
    day_index: int
    et0_mm: float
    etc_mm: float
    effective_rain_mm: float
    irrigation_applied_mm: float
    irrigation_volume_m3: float
    pump_energy_kwh: float
    end_depletion_mm: float
    water_stress_ks: float


@dataclass(frozen=True)
class IrrigationScheduleReport:
    crop_name: str
    area_hectares: float
    days: int
    total_et0_mm: float
    total_etc_mm: float
    total_rainfall_mm: float
    total_irrigation_mm: float
    total_irrigation_m3: float
    total_pump_energy_kwh: float
    irrigation_events: int
    daily: tuple[DailyIrrigationDecision, ...]


def penman_monteith_et0(weather: DailyWeather) -> float:
    """Compute exact FAO-56 Penman-Monteith daily grass reference ET0 (mm/day)."""
    t_mean = 0.5 * (weather.t_min_c + weather.t_max_c)
    # Atmospheric pressure P (kPa) from elevation z (m) — FAO-56 Eq. 7
    pressure_kpa: float = 101.3 * float(((293.0 - 0.0065 * weather.elevation_m) / 293.0) ** 5.26)
    # Psychrometric constant gamma (kPa / C) — FAO-56 Eq. 8
    gamma = 0.000665 * pressure_kpa

    # Saturation vapor pressure e0(T) (kPa) — FAO-56 Eq. 11 & 12
    es_min = 0.6108 * math.exp((17.27 * weather.t_min_c) / (weather.t_min_c + 237.3))
    es_max = 0.6108 * math.exp((17.27 * weather.t_max_c) / (weather.t_max_c + 237.3))
    es = 0.5 * (es_min + es_max)
    ea = es * (max(0.0, min(100.0, weather.rh_mean_pct)) / 100.0)

    # Slope of saturation vapor pressure curve Delta (kPa / C) — FAO-56 Eq. 13
    delta = (4098.0 * (0.6108 * math.exp((17.27 * t_mean) / (t_mean + 237.3)))) / ((t_mean + 237.3) ** 2)

    u2 = max(0.5, weather.wind_2m_ms)  # FAO-56 minimum wind speed floor 0.5 m/s
    rn = weather.net_radiation_mj_m2_day

    # FAO-56 Eq. 6 (soil heat flux G ~= 0 at daily timestep)
    numerator = (0.408 * delta * rn) + (gamma * (900.0 / (t_mean + 273.0)) * u2 * max(0.0, es - ea))
    denominator = delta + gamma * (1.0 + 0.34 * u2)
    return max(0.0, round(numerator / denominator, 3))


def schedule_irrigation(
    weather_days: list[DailyWeather],
    profile: CropSoilProfile,
    *,
    area_hectares: float = 1.0,
    initial_depletion_mm: float = 10.0,
    irrigation_efficiency: float = 0.85,  # Drip = 0.85-0.90, Furrow = 0.60
    pump_head_m: float = 25.0,
    pump_efficiency: float = 0.55,
    deficit_ratio: float = 1.0,  # 1.0 = refill to field capacity; 0.8 = 20% deficit irrigation
) -> IrrigationScheduleReport:
    """Run daily FAO-56 root-zone soil-water balance and compute solar-pump irrigation schedule."""
    if not weather_days:
        raise ValueError("weather_days cannot be empty")
    if area_hectares <= 0 or not 0.1 <= irrigation_efficiency <= 1.0:
        raise ValueError("Invalid area_hectares or irrigation_efficiency")

    taw = profile.taw_mm
    raw_limit = profile.raw_mm
    depletion = max(0.0, min(taw, initial_depletion_mm))
    decisions: list[DailyIrrigationDecision] = []

    for w in weather_days:
        et0 = penman_monteith_et0(w)
        # Water stress coefficient Ks (FAO-56 Eq. 84)
        ks = 1.0 if depletion <= raw_limit else max(0.0, (taw - depletion) / max(1e-6, taw - raw_limit))
        etc = et0 * profile.kc * ks
        eff_rain = max(0.0, w.rainfall_mm * 0.80)  # 80% effective infiltration

        depletion = max(0.0, depletion + etc - eff_rain)
        irrig_net_mm = 0.0
        if depletion >= raw_limit:
            irrig_net_mm = depletion * max(0.1, min(1.0, deficit_ratio))
            depletion = max(0.0, depletion - irrig_net_mm)

        # Gross water depth accounting for application efficiency (1 mm over 1 ha = 10 m^3)
        gross_mm = irrig_net_mm / irrigation_efficiency if irrig_net_mm > 0 else 0.0
        vol_m3 = gross_mm * 10.0 * area_hectares
        pump_kwh = (vol_m3 * pump_head_m * _HYDRAULIC_KWH_PER_M3_M) / max(0.1, pump_efficiency)

        decisions.append(
            DailyIrrigationDecision(
                day_index=w.day_index,
                et0_mm=round(et0, 2),
                etc_mm=round(etc, 2),
                effective_rain_mm=round(eff_rain, 2),
                irrigation_applied_mm=round(gross_mm, 2),
                irrigation_volume_m3=round(vol_m3, 2),
                pump_energy_kwh=round(pump_kwh, 3),
                end_depletion_mm=round(depletion, 2),
                water_stress_ks=round(ks, 3),
            )
        )

    return IrrigationScheduleReport(
        crop_name=profile.crop_name,
        area_hectares=area_hectares,
        days=len(decisions),
        total_et0_mm=round(sum(d.et0_mm for d in decisions), 2),
        total_etc_mm=round(sum(d.etc_mm for d in decisions), 2),
        total_rainfall_mm=round(sum(w.rainfall_mm for w in weather_days), 2),
        total_irrigation_mm=round(sum(d.irrigation_applied_mm for d in decisions), 2),
        total_irrigation_m3=round(sum(d.irrigation_volume_m3 for d in decisions), 2),
        total_pump_energy_kwh=round(sum(d.pump_energy_kwh for d in decisions), 2),
        irrigation_events=sum(1 for d in decisions if d.irrigation_applied_mm > 0),
        daily=tuple(decisions),
    )
