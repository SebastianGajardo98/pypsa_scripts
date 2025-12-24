from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple
from xml.etree import ElementTree as ET
import argparse

import numpy as np
import xarray as xr


def _load_matrix(path: Path) -> Tuple[np.ndarray, List[str]]:
    ds = xr.open_dataset(path)
    data = ds["__xarray_dataarray_variable__"].values
    buses = ds["bus"].astype(str).values.tolist()
    flat = data.reshape(data.shape[0], -1)
    ds.close()
    return flat, buses


def _extend_to_full_day(values: np.ndarray) -> np.ndarray:
    remainder = values.shape[1] % 24
    if remainder == 0:
        return values
    missing = 24 - remainder
    last_column = values[:, -1:].repeat(missing, axis=1)
    return np.concatenate([values, last_column], axis=1)


def run(
    offwind_ac: Path,
    offwind_dc: Path,
    offwind_float: Path,
    onwind: Path,
    output_path: Path,
) -> None:
    tech_files = {
        "profile_offwind-ac": offwind_ac,
        "profile_offwind-dc": offwind_dc,
        "profile_offwind-float": offwind_float,
        "profile_onwind": onwind,
    }

    matrices: Dict[str, np.ndarray] = {}
    bus_lists: Dict[str, List[str]] = {}
    for tech, path in tech_files.items():
        matrix, buses = _load_matrix(path)
        matrix = _extend_to_full_day(matrix)
        matrices[tech] = matrix
        bus_lists[tech] = buses

    all_buses = sorted({bus for buses in bus_lists.values() for bus in buses})
    time_steps = max(mat.shape[1] for mat in matrices.values())

    root = ET.Element("data")
    year_el = ET.SubElement(root, "year")
    year_el.text = "0"

    for t in range(time_steps):
        time_el = ET.SubElement(year_el, "time")
        time_el.text = str(t)

        for bus in all_buses:
            bus_el = ET.SubElement(time_el, bus.replace(" ", ""))
            for tech, matrix in matrices.items():
                if bus in bus_lists[tech]:
                    bus_idx = bus_lists[tech].index(bus)
                    value = matrix[bus_idx, t]
                    cell_value = str(value) if not np.isnan(value) else "None"
                else:
                    cell_value = "None"
                tech_el = ET.SubElement(bus_el, tech)
                tech_el.text = cell_value

    ET.indent(root, space="  ")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(output_path, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert NCRE availability factors.")
    parser.add_argument("--offwind-ac", required=True, type=Path)
    parser.add_argument("--offwind-dc", required=True, type=Path)
    parser.add_argument("--offwind-float", required=True, type=Path)
    parser.add_argument("--onwind", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(
        offwind_ac=args.offwind_ac,
        offwind_dc=args.offwind_dc,
        offwind_float=args.offwind_float,
        onwind=args.onwind,
        output_path=args.output,
    )

