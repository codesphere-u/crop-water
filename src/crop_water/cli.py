"""CLI for crop-water."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from crop_water.fao56 import CropSoilProfile, DailyWeather, schedule_irrigation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crop-water",
        description="FAO-56 Penman-Monteith ET0 & solar-pump drip irrigation scheduler.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo", help="Simulate a 14-day dry-spell smallholder tomato drip irrigation schedule")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "demo":
        weather = [
            DailyWeather(
                day_index=d,
                t_min_c=17.0,
                t_max_c=29.5,
                rh_mean_pct=55.0,
                wind_2m_ms=2.0,
                net_radiation_mj_m2_day=15.5,
                rainfall_mm=18.0 if d == 7 else 0.0,
            )
            for d in range(1, 15)
        ]
        profile = CropSoilProfile(
            "Tomatoes (Mid-Season)",
            kc=1.15,
            root_depth_m=0.6,
            field_capacity_mm_per_m=280.0,
            wilting_point_mm_per_m=130.0,
            depletion_fraction_p=0.40,
        )
        rep = schedule_irrigation(weather, profile, area_hectares=0.5, pump_head_m=20.0)
        print(
            json.dumps(
                {
                    "crop": rep.crop_name,
                    "days": rep.days,
                    "total_et0_mm": rep.total_et0_mm,
                    "total_etc_mm": rep.total_etc_mm,
                    "irrigation_events": rep.irrigation_events,
                    "total_irrigation_m3": rep.total_irrigation_m3,
                    "total_pump_energy_kwh": rep.total_pump_energy_kwh,
                },
                indent=2,
            )
        )
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
