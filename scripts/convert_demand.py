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
        for row in reader:
            if not row or len(row) < 2:
                continue
            timestamp_raw, *values = row
            dt = datetime.strptime(timestamp_raw, "%m/%d/%Y %H:%M")

            period_el = ET.SubElement(
                root, "period", attrib={"timestamp": dt.strftime("%Y-%m-%d %H:%M:%S")}
            )

            for code, value in zip(country_codes, values):
                cell = ET.SubElement(period_el, code)
                cell.text = value

    # Pad last day if incomplete
    periods = list(root.findall("period"))
    if periods:
        total_periods = len(periods)
        remainder = total_periods % 24
        if remainder != 0:
            missing = 24 - remainder
            last_period = periods[-1]
            last_timestamp = last_period.get("timestamp", "")
            last_data = {child.tag: child.text for child in last_period}
            
            # Parse last timestamp to increment
            if last_timestamp:
                try:
                    last_dt = datetime.strptime(last_timestamp, "%Y-%m-%d %H:%M:%S")
                    for i in range(missing):
                        new_dt = last_dt + timedelta(hours=i+1)
                        new_period = ET.SubElement(root, "period", attrib={"timestamp": new_dt.strftime("%Y-%m-%d %H:%M:%S")})
                        for tag, text in last_data.items():
                            cell = ET.SubElement(new_period, tag)
                            cell.text = text
                except ValueError:
                    pass  # Skip padding if timestamp parsing fails

    ET.indent(root, space="  ")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(output_path, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert electricity demand CSV to XML.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.input, args.output)

