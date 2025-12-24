from pathlib import Path
import argparse

from conversion_utils import convert_excel_xml


def run(input_path: Path, output_path: Path) -> None:
    convert_excel_xml(
        input_path=input_path,
        output_path=output_path,
        root_name="data",
        lowercase_headers=False,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert cooling demand XML.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.input, args.output)

