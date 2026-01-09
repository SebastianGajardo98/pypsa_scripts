from __future__ import annotations

from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET
import argparse

import numpy as np
import xarray as xr


def _pad_last_day(values: np.ndarray) -> np.ndarray:
    """If time series is short of a full day, duplicate the last day."""
    remainder = values.shape[0] % 24
    if remainder == 0:
        return values
    missing = 24 - remainder
    tail = values[-remainder:]
    repeats = np.concatenate([tail[-1:]] * (missing // remainder + 1), axis=0)[
        :missing
    ]
    return np.concatenate([values, repeats], axis=0)


def run(input_path: Path, output_path: Path) -> None:
    ds = xr.open_dataset(input_path)
    # Sum all demand components into a single general_demand
    demand_components: Iterable[np.ndarray] = [
        ds[var].values for var in ["residential water", "residential space", "services water", "services space"]
    ]
    summed = np.sum(np.stack(demand_components, axis=0), axis=0)  # (time, node)

    times = ds["snapshots"].values
    nodes = ds["node"].astype(str).values
    ds.close()

    # Ensure full days
    summed = _pad_last_day(summed)
    times = _pad_last_day(times) if summed.shape[0] != times.shape[0] else times

    root = ET.Element("data")
    for idx, ts in enumerate(times):
        row_el = ET.SubElement(root, "row")
        dt = np.datetime64(ts).astype("datetime64[s]").astype(object)
        year = dt.year
        day_of_year = dt.timetuple().tm_yday
        hour = dt.hour
        period_number = (day_of_year - 1) * 24 + hour + 1

        ET.SubElement(row_el, "year").text = str(year)
        ET.SubElement(row_el, "period").text = str(period_number)

        demand_el = ET.SubElement(row_el, "general_demand")
        for node, value in zip(nodes, summed[idx]):
            # Preserve generator names in uppercase, strip spaces.
            col_name = node.replace(" ", "").upper()
            node_el = ET.SubElement(demand_el, col_name)
            node_el.text = str(float(value))

    ET.indent(root, space="  ")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(output_path, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert heat demand NetCDF to XML.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.input, args.output)
