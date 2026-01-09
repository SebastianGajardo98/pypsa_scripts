from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple
from xml.etree import ElementTree as ET
import argparse

import numpy as np
import xarray as xr


def _load_matrix(path: Path) -> Tuple[np.ndarray, List[str], np.ndarray | None]:
    ds = xr.open_dataset(path)
    if "profile" in ds.data_vars:
        da = ds["profile"]
    elif "__xarray_dataarray_variable__" in ds.data_vars:
        da = ds["__xarray_dataarray_variable__"]
    else:
        first_var = next(iter(ds.data_vars))
        da = ds[first_var]

    if "year" in da.dims:
        da = da.isel(year=0)
    if "bin" in da.dims:
        da = da.isel(bin=0)

    if "bus" in da.dims and "time" in da.dims:
        da = da.transpose("bus", "time")

    data = da.values
    buses = ds["bus"].astype(str).values.tolist() if "bus" in ds.coords else []
    times = ds["time"].values if "time" in ds.coords else None
    ds.close()
    return data, buses, times


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
    solar: Path,
    solar_hsat: Path,
    output_path: Path,
) -> None:
    tech_files = {
        "profile_offwind-ac": offwind_ac,
        "profile_offwind-dc": offwind_dc,
        "profile_offwind-float": offwind_float,
        "profile_onwind": onwind,
        "profile_solar": solar,
        "profile_solar-hsat": solar_hsat,
    }

    matrices: Dict[str, np.ndarray] = {}
    bus_lists: Dict[str, List[str]] = {}
    time_arrays: Dict[str, np.ndarray | None] = {}
    valid_buses_by_tech: Dict[str, set[str]] = {}
    for tech, path in tech_files.items():
        matrix, buses, times = _load_matrix(path)
        matrix = _extend_to_full_day(matrix)
        matrices[tech] = matrix
        bus_lists[tech] = buses
        time_arrays[tech] = times
        # Keep only bus columns without any NaN across time.
        valid_buses = set()
        for idx, bus in enumerate(buses):
            if not np.isnan(matrix[idx]).any():
                valid_buses.add(bus)
        valid_buses_by_tech[tech] = valid_buses

    all_buses = sorted({bus for buses in bus_lists.values() for bus in buses})
    time_steps = max(mat.shape[1] for mat in matrices.values())
    time_axis = next((t for t in time_arrays.values() if t is not None), None)
    if time_axis is not None and time_axis.shape[0] < time_steps:
        last = time_axis[-1]
        extra = np.arange(1, time_steps - time_axis.shape[0] + 1, dtype="timedelta64[h]")
        time_axis = np.concatenate([time_axis, last + extra])

    root = ET.Element("data")
    for t in range(time_steps):
        time_el = ET.SubElement(root, "time")
        if time_axis is not None:
            dt = np.datetime64(time_axis[t]).astype("datetime64[s]").astype(object)
            year = dt.year
            period = (dt.timetuple().tm_yday - 1) * 24 + dt.hour + 1
        else:
            year = 0
            period = t + 1
        ET.SubElement(time_el, "year").text = str(year)
        ET.SubElement(time_el, "period").text = str(period)

        for bus in all_buses:
            bus_tag = bus.replace(" ", "_")
            for tech, matrix in matrices.items():
                if bus not in valid_buses_by_tech[tech]:
                    continue
                bus_idx = bus_lists[tech].index(bus)
                value = matrix[bus_idx, t]
                cell_value = str(value)
                tag_name = f"{bus_tag}_{tech}"
                tech_el = ET.SubElement(time_el, tag_name)
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
    parser.add_argument("--solar", required=True, type=Path)
    parser.add_argument("--solar-hsat", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(
        offwind_ac=args.offwind_ac,
        offwind_dc=args.offwind_dc,
        offwind_float=args.offwind_float,
        onwind=args.onwind,
        solar=args.solar,
        solar_hsat=args.solar_hsat,
        output_path=args.output,
    )
