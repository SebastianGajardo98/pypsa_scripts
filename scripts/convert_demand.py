from __future__ import annotations

import csv
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from xml.etree import ElementTree as ET


def run(input_path: Path, output_path: Path) -> None:
    with input_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header or len(header) < 2:
            raise ValueError("CSV header missing or malformed.")

        country_codes = header[1:]

        root = ET.Element("root")
        last_dt = None
        last_values = None
        row_count = 0
        for row in reader:
            if not row or len(row) < 2:
                continue
            timestamp_raw, *values = row
            # Timestamps come as YYYY-MM-DD HH:MM:SS (e.g. 2020-01-01 00:00:00)
            dt = datetime.strptime(timestamp_raw, "%Y-%m-%d %H:%M:%S")
            period_number = (dt.timetuple().tm_yday - 1) * 24 + dt.hour + 1
            row_el = ET.SubElement(root, "row")
            ET.SubElement(row_el, "year").text = str(dt.year)
            ET.SubElement(row_el, "period").text = str(period_number)
            for code, value in zip(country_codes, values):
                cell = ET.SubElement(row_el, code)
                cell.text = value
            last_dt = dt
            last_values = values
            row_count += 1

    # Pad last day if incomplete
    if row_count and last_dt and last_values is not None:
        remainder = row_count % 24
        if remainder != 0:
            missing = 24 - remainder
            for i in range(missing):
                new_dt = last_dt + timedelta(hours=i + 1)
                period_number = (new_dt.timetuple().tm_yday - 1) * 24 + new_dt.hour + 1
                row_el = ET.SubElement(root, "row")
                ET.SubElement(row_el, "year").text = str(new_dt.year)
                ET.SubElement(row_el, "period").text = str(period_number)
                for code, value in zip(country_codes, last_values):
                    cell = ET.SubElement(row_el, code)
                    cell.text = value

    ET.indent(root, space="  ")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(output_path, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert electricity demand CSV to XML.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.input, args.output)
