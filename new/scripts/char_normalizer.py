import os
import re
import sys
import toolkit as tk
from converter import TSV2dict, dict2TSV


approved_chars = r"[a-zA-Z\d ,.+/<>()-:]"


def identify_invalid_chars(string):
    """
    Return a set of invalid characters found in input string.
    """
    invalid_chars = set()
    for char in string:
        m = re.fullmatch(approved_chars, char)
        if not m:
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
    data_item = data_stripped.lower()
    track_changes(data_stripped, data_item, item_change_dict, "lowercase")
    item_change_dict["after_char_normalization"] = data_item
    return data_item, item_change_dict


def normalize_chars(style, data_file, target_column, review_file, reference_file):
    """
    Performs character normalization on target_column in data_file.

    Reads or creates reference & review dicts, performs basic normalization on
    data items, attempts to replace or remove invalid characters in those data
    items if possible, and if no replacement has been specified, adds them to
    review file for manual review.
    """
    data_dict = TSV2dict(data_file)
    char_change_dict = {}
    allowed_chars = set()
    if os.path.isfile(review_file):
        review_dict = TSV2dict(review_file)
    else:
        review_dict = {}
    if os.path.isfile(reference_file):
        reference_dict = TSV2dict(reference_file)
    else:
        reference_dict = {}
    review_dict, reference_dict = tk.update_reference(review_dict, reference_dict)
    review_dict = tk.clean_occurrences(review_dict)
    for index, rowdict in data_dict.items():
        data_item = rowdict[target_column]
        data_item, changes = track_basic_normalization(data_item, index)
        char_change_dict[index] = changes
        invalid_chars = identify_invalid_chars(data_item)
        rowdict["char_validation"] = tk.validate(invalid_chars, "string")
        if tk.validate(invalid_chars, "boolean"):
            rowdict[f"char_normalized_{target_column}"] = data_item
        else:
            review_dict, reference_dict, data_item, allowed_chars = tk.handle_invalid_items(
                style,
                invalid_chars,
                review_dict,
                reference_dict,
                "char",
                data_item,
                allowed_chars
            )
            invalid_chars = identify_invalid_chars(data_item)
            for char in invalid_chars.copy():
                if char in allowed_chars:
                    invalid_chars.remove(char)
            rowdict["char_validation"] = tk.validate(invalid_chars, "string")
            if tk.validate(invalid_chars, "boolean"):
                rowdict[f"char_normalized_{target_column}"] = data_item
            else:
                rowdict[f"char_normalized_{target_column}"] = f"! Invalid characters: {invalid_chars} !"
    output_path = os.path.join(style, "output_files", f"c_norm_{style}.tsv")
    dict2TSV(data_dict, output_path)
    if len(review_dict.keys()) != 0:
        dict2TSV(review_dict, review_file)
    if len(reference_dict.keys()) != 0:
        dict2TSV(reference_dict, reference_file)


if __name__ == "__main__":
    style = sys.argv[1]
    input_file = os.path.join(style, "input_files", sys.argv[2])
    target_column = sys.argv[3]
    review = os.path.join(style, "output_files", "char_review.tsv")
    reference = os.path.join(style, "output_files", "char_reference.tsv")
    normalize_chars(style, input_file, target_column, review, reference)
