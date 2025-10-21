import math
from typing import Any, Dict, Optional

import pandas as pd


def _coerce_value(value: Any) -> Any:
    """Convert pandas NaN values to empty strings for TSV compatibility."""
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return value


def dataframe_to_indexed_dict(df: Optional[pd.DataFrame], index_field: str = "index") -> Dict[int, Dict[str, Any]]:
    """
    Convert a DataFrame into a normalization-style dictionary keyed by index.
    """
    if df is None:
        return {}
    records: Dict[int, Dict[str, Any]] = {}
    for row in df.to_dict(orient="records"):
        if index_field in row and row[index_field] not in [None, ""]:
            try:
                key = int(row[index_field])
            except ValueError:
                key = len(records)
        else:
            key = len(records)
            row[index_field] = key
        records[key] = {k: _coerce_value(v) for k, v in row.items()}
    return records


def dict_to_dataframe(data_dict: Dict[int, Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert a normalization dictionary back into a DataFrame.
    """
    if not data_dict:
        return pd.DataFrame()
    df = pd.DataFrame.from_dict(data_dict, orient="index")
    if "index" in df.columns:
        df["index"] = df["index"].astype(int)
        df = df.sort_values("index")
    else:
        df = df.sort_index()
        df["index"] = df.index
    return df.reset_index(drop=True)


def ensure_dict(obj: Optional[Dict[int, Dict[str, Any]]]) -> Dict[int, Dict[str, Any]]:
    """
    Ensure the provided object is a dictionary compatible with normalization helpers.
    """
    return obj if obj is not None else {}
