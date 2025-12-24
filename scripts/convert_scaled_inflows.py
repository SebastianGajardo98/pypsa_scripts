from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET
import argparse

import numpy as np
import xarray as xr


def run(input_path: Path, output_path: Path) -> None:
    ds = xr.open_dataset(input_path)
    values = ds["__xarray_dataarray_variable__"].values  # (time, countries)
    times = ds["time"].values
    generators = ds["countries"].astype(str).values
    ds.close()

    if values.shape[0] != times.shape[0]:
        raise ValueError("Time axis length mismatch between coordinates and data.")

    remainder = values.shape[0] % 24
    if remainder != 0:
        missing = 24 - remainder
        values = np.concatenate([values, values[-1:, :].repeat(missing, axis=0)], axis=0)
        last_time = times[-1]
        extra = np.arange(1, missing + 1, dtype="timedelta64[h]")
        times = np.concatenate([times, last_time + extra])

    root = ET.Element("root")

    for idx, ts in enumerate(times):
        row_el = ET.SubElement(root, "row")

        ts_dt = np.datetime64(ts).astype("datetime64[s]")
        year_el = ET.SubElement(row_el, "year")
        year_el.text = str(int(str(ts_dt)[:4]))

        period_el = ET.SubElement(row_el, "period")
        period_el.text = str(idx + 1)

        for gen_idx, gen in enumerate(generators):
            gen_el = ET.SubElement(row_el, gen)
            gen_el.text = str(float(values[idx, gen_idx]))

    ET.indent(root, space="  ")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(output_path, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert scaled inflows NetCDF to XML.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.input, args.output)

