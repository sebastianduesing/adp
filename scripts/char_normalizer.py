import os
import re
import sys
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import toolkit as tk
from converter import TSV2dict, dict2TSV
from normalization_utils import (
    dataframe_to_indexed_dict,
    dict_to_dataframe,
    ensure_dict,
)

DEFAULT_APPROVED_CHARS = r"[a-z\d ,.+/<>()\-:_]"


@dataclass
class CharNormalizationResult:
    data: Dict[int, Dict[str, str]]
    review: Dict[int, Dict[str, str]]
    reference: Dict[int, Dict[str, str]]
    changes: Dict[int, Dict[str, str]]


def identify_invalid_chars(string: str, allowed_pattern: str) -> set:
    """
    Return a set of invalid characters found in input string.
    """
    invalid_chars = set()
    for char in string:
        if not re.fullmatch(allowed_pattern, char):
            invalid_chars.add(char)
    return invalid_chars


def track_changes(original_string, new_string, change_dict, tracker_item):
    """
    Logs whether a string was changed at a particular normalization step.
    """
    if original_string != new_string:
        change_dict[tracker_item] = "Y"
    else:
        change_dict[tracker_item] = "N"


def track_basic_normalization(data_item, index):
    """
    Applies basic char normalization to a string and returns change tracker.
    """
    item_change_dict = {}
    item_change_dict["index"] = index
    item_change_dict["before_char_normalization"] = data_item
    data_stripped = tk.normalize_whitespace(data_item)
    track_changes(data_item, data_stripped, item_change_dict, "whitespace")
    item_change_dict["after_char_normalization"] = data_stripped
    return data_stripped, item_change_dict


def normalize_chars_dict(style: str,
                         data_dict: Dict[int, Dict[str, str]],
                         target_column: str,
                         review_dict: Optional[Dict[int, Dict[str, str]]] = None,
                         reference_dict: Optional[Dict[int, Dict[str, str]]] = None,
                         approved_chars_pattern: str = DEFAULT_APPROVED_CHARS
                         ) -> CharNormalizationResult:
    """
    Performs character normalization on target_column in data_file.

    Reads or creates reference & review dicts, performs basic normalization on
    data items, attempts to replace or remove invalid characters in those data
    items if possible, and if no replacement has been specified, adds them to
    review file for manual review.
    """
    output_column = f"char_normalized_{target_column}"
    char_change_dict = {}
    review_dict = ensure_dict(review_dict)
    reference_dict = ensure_dict(reference_dict)
    allowed_chars = set()
    review_dict, reference_dict, allowed_chars = tk.update_reference(review_dict, reference_dict, allowed_chars)
    review_dict = tk.clean_occurrences(review_dict)
    for index, rowdict in data_dict.items():
        data_item = rowdict[target_column]
        data_item, changes = track_basic_normalization(data_item, index)
        char_change_dict[index] = changes
        invalid_chars = identify_invalid_chars(data_item, approved_chars_pattern)
        rowdict["char_validation"] = tk.validate(invalid_chars, "string")
        if tk.validate(invalid_chars, "boolean"):
            rowdict[output_column] = data_item
        else:
            review_dict, reference_dict, data_item, allowed_chars = tk.handle_invalid_items(
                style,
                invalid_chars,
                review_dict,
                reference_dict,
                "char",
                data_item,
                allowed_chars,
                None
            )
            invalid_chars = identify_invalid_chars(data_item, approved_chars_pattern)
            for char in invalid_chars.copy():
                if char in allowed_chars:
                    invalid_chars.remove(char)
            rowdict["char_validation"] = tk.validate(invalid_chars, "string")
            if tk.validate(invalid_chars, "boolean"):
                rowdict[output_column] = data_item
            else:
                rowdict[output_column] = f"! Invalid characters: {sorted(invalid_chars)} !"
        rowdict = tk.evaluate_ld(rowdict,
                                 "char",
                                 target_column,
                                 output_column)
    return CharNormalizationResult(data_dict, review_dict, reference_dict, char_change_dict)


def normalize_chars_dataframe(style: str,
                              dataframe,
                              target_column: str,
                              review_df=None,
                              reference_df=None,
                              approved_chars_pattern: str = DEFAULT_APPROVED_CHARS) -> Tuple:
    """
    Convenience wrapper to run character normalization on pandas DataFrames.
    """
    data_dict = dataframe_to_indexed_dict(dataframe)
    review_dict = dataframe_to_indexed_dict(review_df)
    reference_dict = dataframe_to_indexed_dict(reference_df)
    result = normalize_chars_dict(style,
                                  data_dict,
                                  target_column,
                                  review_dict,
                                  reference_dict,
                                  approved_chars_pattern)
    normalized_df = dict_to_dataframe(result.data)
    review_out_df = dict_to_dataframe(result.review)
    reference_out_df = dict_to_dataframe(result.reference)
    changes_df = dict_to_dataframe(result.changes)
    return normalized_df, review_out_df, reference_out_df, changes_df


def normalize_chars(style, data_file, target_column, review_file, reference_file,
                    approved_chars_pattern: str = DEFAULT_APPROVED_CHARS):
    data_dict = TSV2dict(data_file)
    review_dict = TSV2dict(review_file) if os.path.isfile(review_file) else {}
    reference_dict = TSV2dict(reference_file) if os.path.isfile(reference_file) else {}
    result = normalize_chars_dict(style,
                                  data_dict,
                                  target_column,
                                  review_dict,
                                  reference_dict,
                                  approved_chars_pattern)
    output_path = os.path.join(style, "output_files", f"c_norm_{style}.tsv")
    dict2TSV(result.data, output_path)
    if len(result.review.keys()) != 0:
        dict2TSV(result.review, review_file)
    if len(result.reference.keys()) != 0:
        dict2TSV(result.reference, reference_file)


if __name__ == "__main__":
    style = sys.argv[1]
    input_file = os.path.join(style, "input_files", sys.argv[2])
    target_column = sys.argv[3]
    review = os.path.join(style, "output_files", "char_review.tsv")
    reference = os.path.join(style, "output_files", "char_reference.tsv")
    normalize_chars(style, input_file, target_column, review, reference)
