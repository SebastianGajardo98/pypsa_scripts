# Data Conversion Scripts

This repository contains small converters that turn the provided source files into simplified XML outputs. All generated files are placed in `scripts_generated_data/`.

## How to run everything

```bash
python3 main.py
```

`main.py` wires all converters together, passing every input and output path. It creates `scripts_generated_data/` if it is missing.

## Per-script usage

Every converter accepts explicit `--input`/`--output` (and additional inputs where needed) to avoid hardcoded paths. Examples:

- Cooling demand:  
  `python3 scripts/convert_cooling_demand.py --input data/cooling_demand_HR_2020_2050_sdewes.xml --output scripts_generated_data/cooling_demand_HR_2020_2050_sdewes.xml`

- Electricity demand (CSV → XML):  
  `python3 scripts/convert_demand.py --input data/demand_2020_2050_sdewes/electricity_demand.csv --output scripts_generated_data/demand_2020_2050_sdewes.xml`

- Heat demand (NetCDF → XML):  
  `python3 scripts/convert_heat_demand.py --input data/heat_demand_HR_2020_2050_sdewes/hourly_heat_demand_total_base_s_128.nc --output scripts_generated_data/heat_demand_HR_2020_2050_sdewes.xml`

- Flexible tech COPs (two inputs):  
  `python3 scripts/convert_flex_tech.py --input-2030 data/flex_tech_HR_2020_2050_sdewes/cop_profiles_base_s_128_2030.nc --input-2050 data/flex_tech_HR_2020_2050_sdewes/cop_profiles_base_s_128_2050.nc --output scripts_generated_data/flex_tech_HR_2020_2050_sdewes_explicit.xml`

- NCRE availability factors (four inputs):  
  `python3 scripts/convert_ncre_aval_factor.py --offwind-ac data/ncre_aval_factor_HR_2020_2050_sdewes/availability_matrix_128_offwind-ac.nc --offwind-dc data/ncre_aval_factor_HR_2020_2050_sdewes/availability_matrix_128_offwind-dc.nc --offwind-float data/ncre_aval_factor_HR_2020_2050_sdewes/availability_matrix_128_offwind-float.nc --onwind data/ncre_aval_factor_HR_2020_2050_sdewes/availability_matrix_128_onwind.nc --output scripts_generated_data/ncre_aval_factor_HR_2020_2050_sdewes.xml`

- Scaled inflows:  
  `python3 scripts/convert_scaled_inflows.py --input data/scaled_inflows_HR_2020_2050_sdewes/profile_hydro.nc --output scripts_generated_data/scaled_inflows_HR_2020_2050_sdewes.xml`

Other converters follow the same `--input/--output` pattern (H2 demand, driving cycles, EV transport load, fuel cost, import/export).

## Script reference (what each does)

- `convert_cooling_demand.py`: SpreadsheetML → XML; keeps headers as-is under `<row>`.
- `convert_demand.py`: CSV electricity demand → XML; timestamps on `<period>` and country codes as columns.
- `convert_demand_h2.py`: SpreadsheetML → XML; lowercases headers.
- `convert_driving_cycles.py`: SpreadsheetML → XML for EV driving cycles; lowercases headers.
- `convert_ev_transp_load.py`: SpreadsheetML → XML for EV availability/load.
- `convert_flex_tech.py`: Two NetCDF COP profiles (2030/2050) → explicit XML entries per bus/heat_source/heat_system with `cop_2030`/`cop_2050`.
- `convert_fuel_cost.py`: SpreadsheetML fuel costs → XML; lowercases headers.
- `convert_heat_demand.py`: NetCDF heat demand components → summed `general_demand` XML rows; column names uppercased.
- `convert_import_export.py`: SpreadsheetML import/export → XML; lowercases headers.
- `convert_ncre_aval_factor.py`: Four NetCDF availability matrices → XML per bus/time with offwind/onwind profiles.
- `convert_scaled_inflows.py`: NetCDF hydro inflows → XML rows with year/period and generator columns.
- `conversion_utils.py`: Shared helpers for SpreadsheetML parsing and conversion.
- `main.py`: Orchestrates all converters, wiring paths and writing outputs to `scripts_generated_data/`.
