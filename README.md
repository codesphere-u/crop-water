# crop-water

[![CI](https://github.com/codesphere-u/crop-water/actions/workflows/ci.yml/badge.svg)](https://github.com/codesphere-u/crop-water/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)
[![Zero Dependencies](https://img.shields.io/badge/runtime%20dependencies-0-brightgreen.svg)](pyproject.toml)

**Zero-dependency FAO-56 Penman-Monteith reference evapotranspiration (`ET₀`), daily root-zone soil-water balance, deficit irrigation control, and solar-pump hydraulic energy (`kWh`) scheduler.**

- **Mission Domain:** Climate-Resilient Agriculture & Precision Irrigation
- **Stack:** Pure Python 3.11+ (zero runtime third-party dependencies, `mypy --strict`, `ruff`, `pytest`)
- **Maintainer:** Codesphere Innovations (U) Limited (`codesphere-u`)

---

## Problem Solved

Smallholder farmers adopting solar drip irrigation often over-pump groundwater or under-irrigate during critical dry spells because commercial agronomy suites are paywalled and require cloud connectivity.

## Key Features

- Exact FAO-56 Penman-Monteith daily grass reference `ET₀` (Eq. 6, 7, 8, 11–13) adjusting atmospheric pressure for elevation.
- Daily root-zone Total/Readily Available Water (`TAW`/`RAW`) soil-water depletion tracking with FAO-56 Eq. 84 water-stress coefficient `Ks`.
- Computes gross water depth, irrigation volumes (`m³`), and hydraulic solar-pumping energy requirements (`kWh`) with configurable deficit irrigation.

## Architecture Overview

```mermaid
flowchart LR
  A[Daily Weather & Elevation] --> B[penman_monteith_et0<br/>FAO-56 Eq. 6-13]
  B --> C[Root-Zone TAW/RAW Balance]
  C --> D[Irrigation Volume m3 & Solar Pump kWh]
```

See [docs/architecture.md](docs/architecture.md) for module-level design details.

## Installation

```bash
git clone https://github.com/codesphere-u/crop-water.git
cd crop-water
uv sync --extra dev
```

Or install in editable mode with standard `pip`:

```bash
pip install -e ".[dev]"
```

## Quick Start (CLI)

```bash
crop-water demo
```

## Quick Start (Python API)

```python
from crop_water import DailyWeather, penman_monteith_et0

et0 = penman_monteith_et0(DailyWeather(1, 16.0, 29.0, 55.0, 2.0, 15.0))
assert 4.0 <= et0 <= 6.8
```

## Testing & Quality Gates

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -v
```

## Security, Contributing & Roadmap

- **Security:** See [SECURITY.md](SECURITY.md) for responsible disclosure procedures.
- **Contributing:** See [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
- **Changelog & Roadmap:** See [CHANGELOG.md](CHANGELOG.md) and [ROADMAP.md](ROADMAP.md).

## License

MIT License — see [LICENSE](LICENSE).

## Support & Contact

Open an issue on [GitHub Issues](https://github.com/codesphere-u/crop-water/issues) or contact `codesphereinnovationz@gmail.com`.
