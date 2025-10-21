import argparse
import os
from dataclasses import dataclass
from typing import Dict, List, Tuple

import pandas as pd

from normalization_pipeline import (
    AssetsConfig,
    normalize_csv_to_stream,
)

DEFAULT_TABLES = ("epitope", "mhc_bind", "mhc_elution", "tcell", "bcell")
DEFAULT_COLUMN = "location"
DEFAULT_OUTPUT_DIR = os.path.join("data_loc", "analysis", "normalized_exports")


@dataclass
class TableSpec:
    table: str
    csv_path: str
    target_column: str
    id_columns: Tuple[str, ...]
    new_column_name: str


TABLE_REQUIREMENTS = {
    "epitope": TableSpec(
        table="epitope",
        csv_path="",
        target_column="e_location",
        id_columns=("reference_id", "epitope_id"),
        new_column_name="new e_location",
    ),
    "mhc_bind": TableSpec(
        table="mhc_bind",
        csv_path="",
        target_column="as_location",
        id_columns=("reference_id", "mhc_bind_id"),
        new_column_name="new as_location",
    ),
    "mhc_elution": TableSpec(
        table="mhc_elution",
        csv_path="",
        target_column="as_location",
        id_columns=("reference_id", "mhc_elution_id"),
        new_column_name="new as_location",
    ),
    "tcell": TableSpec(
        table="tcell",
        csv_path="",
        target_column="as_location",
        id_columns=("reference_id", "tcell_id"),
        new_column_name="new as_location",
    ),
    "bcell": TableSpec(
        table="bcell",
        csv_path="",
        target_column="as_location",
        id_columns=("reference_id", "bcell_id"),
        new_column_name="new as_location",
    ),
}


def parse_table_specs(specs: List[str], default_column: str, input_dir: str) -> List[TableSpec]:
    parsed: List[TableSpec] = []
    for spec in specs:
        if ":" in spec:
            table_name, column = spec.split(":", 1)
        else:
            table_name, column = spec, ""
        table_name = table_name.strip()
        if not table_name:
            continue
        requirement = TABLE_REQUIREMENTS.get(table_name)
        if requirement:
            target_column = column.strip() or requirement.target_column
            id_columns = requirement.id_columns
            new_column = requirement.new_column_name
        else:
            target_column = column.strip() or default_column
            id_columns = ("reference_id", f"{table_name}_id")
            new_column = f"new {target_column}"
        csv_path = os.path.join(input_dir, f"{table_name}.csv")
        parsed.append(TableSpec(
            table=table_name,
            csv_path=csv_path,
            target_column=target_column,
            id_columns=id_columns,
            new_column_name=new_column,
        ))
    return parsed


def validate_csv(spec: TableSpec) -> None:
    if not os.path.isfile(spec.csv_path):
        raise FileNotFoundError(f"Expected CSV for table '{spec.table}' at {spec.csv_path}")
    sample = pd.read_csv(spec.csv_path, nrows=0)
    missing_cols = [col for col in (*spec.id_columns, spec.target_column) if col not in sample.columns]
    if missing_cols:
        raise ValueError(f"CSV {spec.csv_path} missing required columns {missing_cols}")


def main():
    parser = argparse.ArgumentParser(description="Normalize CSV exports into per-table normalized CSV outputs.")
    parser.add_argument(
        "--input-dir",
        default=os.path.join("data_loc", "input_files", "sql_exports"),
        help="Directory containing CSVs named <table>.csv",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where normalized <table>-normalized.csv files will be written.",
    )
    parser.add_argument(
        "--tables",
        nargs="*",
        default=list(DEFAULT_TABLES),
        help="Tables to process. Override column via table:column (default location column varies per table).",
    )
    parser.add_argument(
        "--default-column",
        default=DEFAULT_COLUMN,
        help="Fallback location column name when table not in default list.",
    )
    parser.add_argument(
        "--assets-dir",
        default="data_loc",
        help="Root directory containing review/reference assets (expects output_files/*).",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=50000,
        help="Number of rows to process per chunk (use <=0 to load the entire file at once).",
    )
    parser.add_argument(
        "--persist-assets",
        action="store_true",
        help="Persist updated review/reference dictionaries back to disk after each chunk.",
    )
    args = parser.parse_args()

    os.makedirs(args.input_dir, exist_ok=True)
    os.makedirs(args.output_dir, exist_ok=True)

    table_specs = parse_table_specs(args.tables, args.default_column, args.input_dir)

    assets = AssetsConfig(style="data_loc", base_dir=args.assets_dir)

    summary_rows = []
    for spec in table_specs:
        validate_csv(spec)
        output_path = os.path.join(args.output_dir, f"{spec.table}-normalized.csv")
        total = normalize_csv_to_stream(
            csv_path=spec.csv_path,
            table_name=spec.table,
            target_column=spec.target_column,
            id_columns=spec.id_columns,
            new_column_name=spec.new_column_name,
            assets=assets,
            output_csv_path=output_path,
            chunk_size=args.chunk_size,
            persist_assets=args.persist_assets,
        )
        summary_rows.append({
            "table": spec.table,
            "rows_written": total,
            "output": output_path,
        })
        print(f"{spec.table}: {total} rows written to {output_path}")

    summary_df = pd.DataFrame(summary_rows)
    summary_path = os.path.join(args.output_dir, "normalized_summary.csv")
    summary_df.to_csv(summary_path, index=False)
    print(f"Summary written to {summary_path}")


if __name__ == "__main__":
    main()
