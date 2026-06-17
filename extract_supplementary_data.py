from __future__ import annotations

import argparse
import csv
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent
DEFAULT_DOCX = Path(r"C:\Users\Administrator\Downloads\1-s2.0-S2666546825000096-mmc1.docx")
DEFAULT_OUTPUT = ROOT / "data" / "supplementary_co2_adsorbents.csv"
WORD_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

OUTPUT_COLUMNS = [
    "sample_id",
    "reference",
    "surface_area_before",
    "surface_area_after",
    "pore_volume_before",
    "pore_volume_after",
    "amine_type",
    "molecular_weight",
    "nitrogen_atom_content",
    "primary_amine_proportion",
    "secondary_amine_proportion",
    "tertiary_amine_proportion",
    "amine_loading",
    "temperature",
    "co2_partial_pressure",
    "relative_humidity",
    "co2_adsorbed_amount",
]


def element_text(element: ET.Element) -> str:
    return "".join(text.text or "" for text in element.findall(".//w:t", WORD_NS)).strip()


def parse_float(value: str) -> float:
    cleaned = value.strip().replace(",", "")
    if cleaned in {"", "-", "NA", "N/A"}:
        raise ValueError("missing numeric value")
    return float(cleaned)


def read_docx_table_rows(path: Path, table_index: int = 0) -> list[list[str]]:
    with ZipFile(path) as docx:
        root = ET.fromstring(docx.read("word/document.xml"))
    tables = root.findall(".//w:tbl", WORD_NS)
    if table_index >= len(tables):
        raise ValueError(f"Table index {table_index} not found; document has {len(tables)} tables.")
    rows: list[list[str]] = []
    for row in tables[table_index].findall("./w:tr", WORD_NS):
        rows.append([element_text(cell) for cell in row.findall("./w:tc", WORD_NS)])
    return rows


def extract_table_s1_1(path: Path) -> list[dict[str, object]]:
    rows = read_docx_table_rows(path, table_index=0)
    data_rows = rows[2:]
    records: list[dict[str, object]] = []
    current_ref = ""
    per_ref_index: dict[str, int] = {}

    for row in data_rows:
        if len(row) != 16:
            continue
        ref = row[0].strip() or current_ref
        if not ref:
            continue
        current_ref = ref
        per_ref_index[ref] = per_ref_index.get(ref, 0) + 1
        sample_id = f"{ref}_{per_ref_index[ref]:03d}"

        try:
            records.append(
                {
                    "sample_id": sample_id,
                    "reference": ref,
                    "surface_area_before": parse_float(row[1]),
                    "surface_area_after": parse_float(row[2]),
                    "pore_volume_before": parse_float(row[3]),
                    "pore_volume_after": parse_float(row[4]),
                    "amine_type": row[5].strip(),
                    "molecular_weight": parse_float(row[6]),
                    "nitrogen_atom_content": parse_float(row[7]),
                    "primary_amine_proportion": parse_float(row[8]),
                    "secondary_amine_proportion": parse_float(row[9]),
                    "tertiary_amine_proportion": parse_float(row[10]),
                    "amine_loading": parse_float(row[11]),
                    "temperature": parse_float(row[12]),
                    "co2_partial_pressure": parse_float(row[13]),
                    "relative_humidity": parse_float(row[14]),
                    "co2_adsorbed_amount": parse_float(row[15]),
                }
            )
        except ValueError:
            continue

    return records


def write_csv(records: list[dict[str, object]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(records)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract Table S1-1 from the supplementary DOCX.")
    parser.add_argument("--docx", type=Path, default=DEFAULT_DOCX)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    records = extract_table_s1_1(args.docx)
    if not records:
        raise SystemExit("No valid records were extracted from Table S1-1.")
    write_csv(records, args.output)
    print(f"Extracted {len(records)} records to {args.output.resolve()}")


if __name__ == "__main__":
    main()
