from __future__ import annotations

from pathlib import Path
from typing import List, Tuple
from xml.etree import ElementTree as ET


def _strip_namespaces(tree: ET.ElementTree) -> ET.ElementTree:
    """Remove XML namespaces to simplify tag lookups."""
    root = tree.getroot()
    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]
        elem.attrib = {k.split("}", 1)[-1]: v for k, v in elem.attrib.items()}
    return tree


def _parse_row(row: ET.Element) -> List[str]:
    """
    Extract ordered cell values from a SpreadsheetML Row element,
    respecting optional column indexes (ss:Index).
    """
    cells: List[str] = []
    col_idx = 1
    for cell in row.findall("Cell"):
        index_attr = next(
            (v for k, v in cell.attrib.items() if k.endswith("Index")), None
        )
        if index_attr:
            target = int(index_attr)
            while col_idx < target:
                cells.append("")
                col_idx += 1
        data = cell.find("Data")
        cells.append("" if data is None or data.text is None else data.text)
        col_idx += 1
    return cells


def _string_row_length(row: ET.Element) -> Tuple[int, int]:
    """
    Return a sortable tuple indicating whether a row is all strings and its length.
    Used to pick the header row among candidates.
    """
    cells = row.findall("Cell")
    if not cells:
        return (0, 0)
    is_all_string = all(
        (cell.find("Data") is not None)
        and cell.find("Data").attrib.get("Type", cell.find("Data").attrib.get("type"))
        == "String"
        for cell in cells
    )
    return (1 if is_all_string else 0, len(cells))


def convert_excel_xml(
    input_path: Path,
    output_path: Path,
    *,
    root_name: str = "root",
    lowercase_headers: bool = False,
) -> None:
    """
    Convert a SpreadsheetML file exported from Excel into a simple XML structure.

    The converter:
    - picks the string-only Row with the most cells as the header row
    - lowercases headers if requested
    - writes rows as <row><col>value</col>...</row> under the chosen root
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    tree = _strip_namespaces(ET.parse(input_path))
    rows = tree.findall(".//Worksheet/Table/Row")
    if not rows:
        raise ValueError(f"No rows found in {input_path}")

    header_idx, header_row = max(
        ((idx, row) for idx, row in enumerate(rows)),
        key=lambda pair: _string_row_length(pair[1]),
    )
    headers = _parse_row(header_row)
    if lowercase_headers:
        headers = [header.lower() for header in headers]

    root_el = ET.Element(root_name)

    for row in rows[header_idx + 1 :]:
        values = _parse_row(row)
        if not values or all(value == "" for value in values):
            continue

        # Align with header length
        if len(values) < len(headers):
            values.extend([""] * (len(headers) - len(values)))
        values = values[: len(headers)]

        row_el = ET.SubElement(root_el, "row")
        for col_name, value in zip(headers, values):
            col_name = col_name.strip()
            if not col_name:
                continue
            cell_el = ET.SubElement(row_el, col_name)
            cell_el.text = value

    ET.indent(root_el, space="  ")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root_el).write(
        output_path, encoding="utf-8", xml_declaration=True
    )
    
    # Pad last day if incomplete
    _pad_last_day_xml(output_path)


def _pad_last_day_xml(xml_path: Path) -> None:
    """
    Pad the last day in an XML file if it has fewer than 24 periods.
    Works with XML files that have <row> elements with <year> and <period> children.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    rows = list(root.findall("row"))
    if not rows:
        return
    
    # Get last period number
    last_row = rows[-1]
    period_elem = last_row.find("period")
    if period_elem is None:
        return
    
    try:
        last_period = int(period_elem.text)
    except (ValueError, TypeError):
        return
    
    remainder = last_period % 24
    if remainder == 0:
        return  # Already complete
    
    missing = 24 - remainder
    last_row_data = {child.tag: child.text for child in last_row}
    
    # Duplicate last row for missing periods
    for i in range(missing):
        new_period = last_period + i + 1
        new_row = ET.SubElement(root, "row")
        
        # Copy all fields from last row
        for tag, text in last_row_data.items():
            if tag == "period":
                period_el = ET.SubElement(new_row, "period")
                period_el.text = str(new_period)
            else:
                field_el = ET.SubElement(new_row, tag)
                field_el.text = text
    
    ET.indent(root, space="  ")
    tree.write(xml_path, encoding="utf-8", xml_declaration=True)

