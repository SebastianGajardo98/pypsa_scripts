import os
from pathlib import Path
import sys

# Ensure we can import modules from the local scripts directory.
PROJECT_ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

# Configurables via entorno (Colab/Drive)
DRIVE_PREFIX = Path(
    os.environ.get("DRIVE_PREFIX", "/content/drive/MyDrive/pypsa-eur/resources")
)
CLUSTERS_SUFFIX = os.environ.get("CLUSTERS_SUFFIX", "128")

from convert_cooling_demand import run as convert_cooling_demand  # noqa: E402
from convert_demand_h2 import run as convert_demand_h2  # noqa: E402
from convert_demand import run as convert_demand  # noqa: E402
from convert_driving_cycles import run as convert_driving_cycles  # noqa: E402
from convert_ev_transp_load import run as convert_ev_transp_load  # noqa: E402
from convert_flex_tech import run as convert_flex_tech  # noqa: E402
from convert_fuel_cost import run as convert_fuel_cost  # noqa: E402
from convert_heat_demand import run as convert_heat_demand  # noqa: E402
from convert_import_export import run as convert_import_export  # noqa: E402
from convert_ncre_aval_factor import run as convert_ncre_aval_factor  # noqa: E402
from convert_scaled_inflows import run as convert_scaled_inflows  # noqa: E402


def main() -> None:
    data_dir = PROJECT_ROOT / "data"
    # Allow overriding the export folder via env; default to a top-level path (e.g. for Colab)
    export_folder = os.environ.get("H2RES_EXPORT_FOLDER", "/content/h2res_export_folder")
    out_dir = Path(export_folder)
    out_dir.mkdir(exist_ok=True)

    # Read data from Drive (parametrizado por CLUSTERS_SUFFIX)
    convert_demand(
        input_path=DRIVE_PREFIX / "electricity_demand.csv",
        output_path=out_dir / "demand_2020_2050.xml",
    )
    convert_flex_tech(
        input_2030=DRIVE_PREFIX / f"cop_profiles_base_s_{CLUSTERS_SUFFIX}_2030.nc",
        input_2050=DRIVE_PREFIX / f"cop_profiles_base_s_{CLUSTERS_SUFFIX}_2050.nc",
        output_path=out_dir / "flex_tech_2020_2050_explicit.xml",
    )
    convert_heat_demand(
        input_path=DRIVE_PREFIX / f"hourly_heat_demand_total_base_s_{CLUSTERS_SUFFIX}.nc",
        output_path=out_dir / "heat_demand_2020_2050.xml",
    )
    convert_ncre_aval_factor(
        offwind_ac=DRIVE_PREFIX / f"availability_matrix_{CLUSTERS_SUFFIX}_offwind-ac.nc",
        offwind_dc=DRIVE_PREFIX / f"availability_matrix_{CLUSTERS_SUFFIX}_offwind-dc.nc",
        offwind_float=DRIVE_PREFIX / f"availability_matrix_{CLUSTERS_SUFFIX}_offwind-float.nc",
        onwind=DRIVE_PREFIX / f"availability_matrix_{CLUSTERS_SUFFIX}_onwind.nc",
        output_path=out_dir / "ncre_aval_factor_2020_2050.xml",
    )
    convert_scaled_inflows(
        input_path=DRIVE_PREFIX / "profile_hydro.nc",
        output_path=out_dir / "scaled_inflows_2020_2050.xml",
    )

    # Read data from data directory (local)
    convert_cooling_demand(
        input_path=data_dir / "cooling_demand_2020_2050.xml",
        output_path=out_dir / "cooling_demand_2020_2050.xml",
    )
    convert_demand_h2(
        input_path=data_dir / "demand_H2_2020_2050.xml",
        output_path=out_dir / "demand_H2_2020_2050.xml",
    )
    convert_driving_cycles(
        input_path=data_dir / "driving_cycles_scaled_1MWh.xml",
        output_path=out_dir / "driving_cycles_scaled_1MWh.xml",
    )
    convert_ev_transp_load(
        input_path=data_dir / "ev_transp_load.xml",
        output_path=out_dir / "ev_transp_load.xml",
    )
    convert_fuel_cost(
        input_path=data_dir / "fuel_cost_2020_2050.xml",
        output_path=out_dir / "fuel_cost_2020_2050.xml",
    )
    convert_import_export(
        input_path=data_dir / "import_export_2020_2050.xml",
        output_path=out_dir / "import_export_2020_2050.xml",
    )


if __name__ == "__main__":
    main()
