from __future__ import annotations

from pathlib import Path
from typing import Tuple
from xml.etree import ElementTree as ET
import argparse

import numpy as np
import xarray as xr


def _pad_last_day(values: np.ndarray) -> np.ndarray:
    """Ensure time dimension covers a full day by duplicating last available hours."""
    remainder = values.shape[-1] % 24
    if remainder == 0:
        return values
    missing = 24 - remainder
    last_slice = values[..., -1:]
    padding = np.repeat(last_slice, missing, axis=-1)
    return np.concatenate([values, padding], axis=-1)


def _load_profiles(path: Path) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Tuple[np.ndarray, np.ndarray]]:
    ds = xr.open_dataset(path)
    data = ds["__xarray_dataarray_variable__"].values  # (heat_system, heat_source, time, name)
    time = ds["time"].values
    names = ds["name"].astype(str).values
    heat_source = ds["heat_source"].astype(str).values
    heat_system = ds["heat_system"].astype(str).values
    ds.close()
    return data, time, names, (heat_source, heat_system)


def run(input_2030: Path, input_2050: Path, output_path: Path) -> None:
    data_2030, time_2030, names, meta = _load_profiles(input_2030)
    data_2050, time_2050, names_2050, meta_2050 = _load_profiles(input_2050)

    if list(names) != list(names_2050):
        raise ValueError("Bus/name lists differ between 2030 and 2050 datasets.")

    heat_source, heat_system = meta
    hs_2050, sys_2050 = meta_2050
    if list(heat_source) != list(hs_2050) or list(heat_system) != list(sys_2050):
        raise ValueError("Heat source/system lists differ between datasets.")
    # Align time lengths, padding the shorter one
    if data_2030.shape[-1] != data_2050.shape[-1]:
        data_2030 = _pad_last_day(data_2030)
        data_2050 = _pad_last_day(data_2050)
        max_time = max(data_2030.shape[-1], data_2050.shape[-1])
        if data_2030.shape[-1] < max_time:
            pad = np.repeat(data_2030[..., -1:], max_time - data_2030.shape[-1], axis=-1)
            data_2030 = np.concatenate([data_2030, pad], axis=-1)
        if data_2050.shape[-1] < max_time:
            pad = np.repeat(data_2050[..., -1:], max_time - data_2050.shape[-1], axis=-1)
            data_2050 = np.concatenate([data_2050, pad], axis=-1)
    else:
        data_2030 = _pad_last_day(data_2030)
        data_2050 = _pad_last_day(data_2050)

    # Use the longer/padded time axis
    time_axis = time_2030 if data_2030.shape[-1] >= data_2050.shape[-1] else time_2050
    if time_axis.shape[0] < data_2030.shape[-1]:
        # extend time axis with last timestamp hourly increments
        last = time_axis[-1]
        extra = np.arange(1, data_2030.shape[-1] - time_axis.shape[0] + 1, dtype="timedelta64[h]")
        time_axis = np.concatenate([time_axis, last + extra])

    root = ET.Element("data")
    for t_idx, ts in enumerate(time_axis):
        time_el = ET.SubElement(root, "time")
        time_el.text = str(np.datetime_as_string(ts, unit="s")).replace("T", " ")

        for n_idx, name in enumerate(names):
            bus_el = ET.SubElement(time_el, name.replace(" ", "_").lower())
            for hs_idx, hs in enumerate(heat_source):
                for sys_idx, sys in enumerate(heat_system):
                    entry_el = ET.SubElement(bus_el, "entry")
                    ET.SubElement(entry_el, "heat_source").text = hs
                    ET.SubElement(entry_el, "heat_system").text = sys
                    ET.SubElement(entry_el, "cop_2030").text = str(
                        float(data_2030[sys_idx, hs_idx, t_idx, n_idx])
                    )
                    ET.SubElement(entry_el, "cop_2050").text = str(
                        float(data_2050[sys_idx, hs_idx, t_idx, n_idx])
                    )

    ET.indent(root, space="  ")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(output_path, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert flexible tech COP profiles.")
    parser.add_argument("--input-2030", required=True, type=Path)
    parser.add_argument("--input-2050", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.input_2030, args.input_2050, args.output)

