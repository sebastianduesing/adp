import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

import pandas as pd

from converter import dict2TSV
from data_loc_unsplitter import unsplit
from normalization_utils import (
    dataframe_to_indexed_dict,
    dict_to_dataframe,
)
from phrase_normalizer import (
    DEFAULT_SEPARATOR,
    normalize_phrase_dict,
)
from word_normalizer import (
    DEFAULT_APPROVED_WORDS,
    DEFAULT_DELIMITERS,
    normalize_words_dict,
)
from char_normalizer import (
    DEFAULT_APPROVED_CHARS,
    normalize_chars_dict,
)


def _load_assets_dict(path: Optional[str]) -> Dict[int, Dict[str, str]]:
    if path is None or not os.path.isfile(path):
        return {}
    df = pd.read_csv(path, sep="\t", dtype=str).fillna("")
    return dataframe_to_indexed_dict(df)


def _persist_dict(path: Optional[str], data: Dict[int, Dict[str, str]]) -> None:
    if path is None:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    dict2TSV(data, path)


@dataclass
class AssetsConfig:
    style: str = "data_loc"
    base_dir: Optional[str] = None
    approved_chars_pattern: str = DEFAULT_APPROVED_CHARS
    approved_words: Sequence[str] = tuple(DEFAULT_APPROVED_WORDS)
    delimiters: Sequence[str] = tuple(DEFAULT_DELIMITERS)
    separator: str = DEFAULT_SEPARATOR
    char_review_path: Optional[str] = None
    char_reference_path: Optional[str] = None
    word_review_path: Optional[str] = None
    word_reference_path: Optional[str] = None
    phrase_types_path: Optional[str] = None

    def resolved(self) -> "AssetsConfig":
        if not self.base_dir:
            return self
        output_dir = os.path.join(self.base_dir, "output_files")
        return AssetsConfig(
            style=self.style,
            base_dir=self.base_dir,
            approved_chars_pattern=self.approved_chars_pattern,
            approved_words=self.approved_words,
            delimiters=self.delimiters,
            separator=self.separator,
            char_review_path=self.char_review_path or os.path.join(output_dir, "char_review.tsv"),
            char_reference_path=self.char_reference_path or os.path.join(output_dir, "char_reference.tsv"),
            word_review_path=self.word_review_path or os.path.join(output_dir, "word_review.tsv"),
            word_reference_path=self.word_reference_path or os.path.join(output_dir, "word_reference.tsv"),
            phrase_types_path=self.phrase_types_path or os.path.join(output_dir, f"{self.style}_phrase_types.tsv"),
        )


@dataclass
class TableConfig:
    name: str
    dataframe: pd.DataFrame
    target_column: str
    id_columns: Sequence[str] = ()
    new_column_name: str = "new_location"


@dataclass
class TableNormalizationResult:
    table: str
    export_df: pd.DataFrame
    clean_df: pd.DataFrame
    char_df: pd.DataFrame
    word_df: pd.DataFrame
    phrase_df: pd.DataFrame
    char_review_df: pd.DataFrame
    word_review_df: pd.DataFrame
    char_reference_df: pd.DataFrame
    word_reference_df: pd.DataFrame
    phrase_types_df: pd.DataFrame


def _normalize_series(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def _build_export_dataframe(clean_df: pd.DataFrame, config: TableConfig) -> pd.DataFrame:
    if clean_df.empty:
        return pd.DataFrame(columns=[*config.id_columns, config.target_column, config.new_column_name])

    df = clean_df.copy()
    if "clean_output" not in df.columns:
        df["clean_output"] = ""

    required_columns = list(config.id_columns) + [config.target_column, "clean_output"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise KeyError(f"Missing expected columns for table '{config.name}': {missing_columns}")

    df = df[_normalize_series(df["clean_output"]) != ""]

    original_series = _normalize_series(df[config.target_column])
    new_series = _normalize_series(df["clean_output"])
    mask = (
        (original_series != "") &
        (new_series != "") &
        (original_series != new_series)
    )
    filtered_df = df[mask].copy()

    if filtered_df.empty:
        return pd.DataFrame(columns=[*config.id_columns, config.target_column, config.new_column_name])

    filtered_df[config.new_column_name] = new_series.loc[filtered_df.index]
    export_columns = list(config.id_columns) + [config.target_column, config.new_column_name]
    export_df = filtered_df.loc[:, export_columns].drop_duplicates()
    return export_df.reset_index(drop=True)


def normalize_table(config: TableConfig,
                    assets: AssetsConfig,
                    persist_assets: bool = False) -> TableNormalizationResult:
    resolved_assets = assets.resolved()
    base_df = config.dataframe.copy()
    base_df = base_df.fillna("")
    base_df["index"] = base_df.index.astype(int)

    char_review_dict = _load_assets_dict(resolved_assets.char_review_path)
    char_reference_dict = _load_assets_dict(resolved_assets.char_reference_path)
    word_review_dict = _load_assets_dict(resolved_assets.word_review_path)
    word_reference_dict = _load_assets_dict(resolved_assets.word_reference_path)
    phrase_types_dict = _load_assets_dict(resolved_assets.phrase_types_path)

    char_result = normalize_chars_dict(
        resolved_assets.style,
        dataframe_to_indexed_dict(base_df),
        config.target_column,
        review_dict=char_review_dict,
        reference_dict=char_reference_dict,
        approved_chars_pattern=resolved_assets.approved_chars_pattern,
    )
    char_df = dict_to_dataframe(char_result.data)
    char_review_df = dict_to_dataframe(char_result.review)
    char_reference_df = dict_to_dataframe(char_result.reference)

    word_result = normalize_words_dict(
        resolved_assets.style,
        char_result.data,
        config.target_column,
        review_dict=word_review_dict,
        reference_dict=word_reference_dict,
        approved_words=resolved_assets.approved_words,
        delimiters=resolved_assets.delimiters,
    )
    word_df = dict_to_dataframe(word_result.data)
    word_review_df = dict_to_dataframe(word_result.review)
    word_reference_df = dict_to_dataframe(word_result.reference)

    phrase_result = normalize_phrase_dict(
        resolved_assets.style,
        word_result.data,
        config.target_column,
        word_review_dict=word_result.review,
        word_reference_dict=word_result.reference,
        type_dict=phrase_types_dict,
        separator=resolved_assets.separator,
    )
    phrase_df = dict_to_dataframe(phrase_result.data)
    phrase_types_df = dict_to_dataframe(phrase_result.type_dict)

    unsplit_dict = unsplit(
        phrase_result.data.copy(),
        config.target_column,
        include_partial=True,
        drop_intermediate=False,
    )
    clean_df = dict_to_dataframe(unsplit_dict)

    export_df = _build_export_dataframe(clean_df, config)

    if persist_assets:
        _persist_dict(resolved_assets.char_review_path, char_result.review)
        _persist_dict(resolved_assets.char_reference_path, char_result.reference)
        _persist_dict(resolved_assets.word_review_path, word_result.review)
        _persist_dict(resolved_assets.word_reference_path, word_result.reference)
        _persist_dict(resolved_assets.phrase_types_path, phrase_result.type_dict)

    return TableNormalizationResult(
        table=config.name,
        export_df=export_df,
        clean_df=clean_df,
        char_df=char_df,
        word_df=word_df,
        phrase_df=phrase_df,
        char_review_df=char_review_df,
        word_review_df=word_review_df,
        char_reference_df=char_reference_df,
        word_reference_df=word_reference_df,
        phrase_types_df=phrase_types_df,
    )


def export_results_to_excel(results: List[TableNormalizationResult],
                            output_path: str,
                            include_intermediate: bool = False) -> None:
    EXCEL_MAX_ROWS = 1_048_576
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    summary_rows = []
    overflow_exports = []
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for result in results:
            row_count = len(result.export_df)
            sheet_name = result.table[:31]
            if row_count == 0:
                summary_rows.append({
                    "table": result.table,
                    "total_rows_meeting_criteria": 0,
                    "export_target": "skipped",
                })
                continue

            if row_count > EXCEL_MAX_ROWS:
                base_dir = os.path.dirname(output_path)
                base_name = os.path.splitext(os.path.basename(output_path))[0]
                csv_path = os.path.join(base_dir, f"{base_name}_{result.table}.csv")
                result.export_df.to_csv(csv_path, index=False)
                overflow_exports.append({"table": result.table, "path": csv_path})
                export_target = f"csv:{os.path.basename(csv_path)}"
            else:
                result.export_df.to_excel(writer, sheet_name=sheet_name, index=False)
                export_target = f"sheet:{sheet_name}"

            summary_rows.append({
                "table": result.table,
                "total_rows_meeting_criteria": row_count,
                "export_target": export_target,
            })

            if include_intermediate:
                intermediate_specs = [
                    (result.char_df, f"{result.table[:28]}_char", "char"),
                    (result.word_df, f"{result.table[:28]}_word", "word"),
                    (result.phrase_df, f"{result.table[:27]}_phrase", "phrase"),
                ]
                for df, sheet, tag in intermediate_specs:
                    if df.empty:
                        continue
                    if len(df) > EXCEL_MAX_ROWS:
                        base_dir = os.path.dirname(output_path)
                        base_name = os.path.splitext(os.path.basename(output_path))[0]
                        csv_path = os.path.join(base_dir, f"{base_name}_{result.table}_{tag}.csv")
                        df.to_csv(csv_path, index=False)
                        overflow_exports.append({"table": f"{result.table} ({tag})", "path": csv_path})
                        continue
                    df.to_excel(writer, sheet_name=sheet, index=False)

        summary_df = pd.DataFrame(summary_rows)
        summary_df.to_excel(writer, sheet_name="summary", index=False)

    if overflow_exports:
        notice_lines = ["The following tables exceeded Excel worksheet row limits and were exported as CSV files:"]
        for entry in overflow_exports:
            notice_lines.append(f"- {entry['table']}: {entry['path']}")
        notice_path = os.path.join(os.path.dirname(output_path), "large_table_exports.txt")
        with open(notice_path, "w", encoding="utf-8") as notice_file:
            notice_file.write("\n".join(notice_lines))


def normalize_tables_to_excel(tables: List[TableConfig],
                              assets: AssetsConfig,
                              excel_path: str,
                              persist_assets: bool = False,
                              include_intermediate: bool = False) -> List[TableNormalizationResult]:
    results = []
    for table in tables:
        results.append(normalize_table(table, assets, persist_assets=persist_assets))
    export_results_to_excel(results, excel_path, include_intermediate=include_intermediate)
    return results


def normalize_csv_to_stream(csv_path: str,
                            table_name: str,
                            target_column: str,
                            id_columns: Sequence[str],
                            new_column_name: str,
                            assets: AssetsConfig,
                            output_csv_path: str,
                            chunk_size: Optional[int] = None,
                            persist_assets: bool = True) -> int:
    """
    Normalize a large CSV in manageable chunks and stream updated rows to an output CSV.
    Returns the total number of rows written.
    """
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    total_rows = 0
    header_written = False

    if chunk_size is None or chunk_size <= 0:
        chunks = [pd.read_csv(csv_path, dtype=str, keep_default_na=False)]
    else:
        chunks = pd.read_csv(csv_path, dtype=str, keep_default_na=False, chunksize=chunk_size)

    for chunk in chunks:
        if chunk.empty:
            continue
        config = TableConfig(
            name=table_name,
            dataframe=chunk,
            target_column=target_column,
            id_columns=id_columns,
            new_column_name=new_column_name,
        )
        result = normalize_table(config, assets, persist_assets=persist_assets)
        export_df = result.export_df
        if export_df.empty:
            continue
        mode = "w" if not header_written else "a"
        export_df.to_csv(output_csv_path, index=False, mode=mode, header=not header_written)
        header_written = True
        total_rows += len(export_df)

    if not header_written:
        pd.DataFrame(columns=[*id_columns, target_column, new_column_name]).to_csv(output_csv_path, index=False)

    return total_rows
