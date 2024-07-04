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


def take_action(reference_dict, invalid_char, data_item, index):
    """
    Alters data_item as specified in reference_dict.

    This may be moved to toolkit later; I have suspicions that word
    substitution will require more finesse (dealing with punctuation and
    delimiters, etc.), so it will probably be preferable to just build out a
    word-specific version of this function. To be determined.
    """
    if reference_dict[index]["replace_with"] != "":
        replacement = reference_dict[index]["replace_with"]
        data_item = re.sub(invalid_char, replacement, data_item)
    elif reference_dict[index]["remove"] != "":
        data_item = re.sub(invalid_char, "", data_item)
    return data_item


def track_changes(original_string, new_string, change_dict, tracker_item):
    """
    Logs whether a string was changed at a particular normalization step.
    """
    if original_string != new_string:
        change_dict[tracker_item] = "Y"
    else:
        change_dict[tracker_item] = "N"


def basic_normalize(data_item, index):
    """
    Applies basic char normalization to a string and returns change tracker.
    """
    item_change_dict = {}
    item_change_dict["index"] = index
    item_change_dict["before_char_normalization"] = data_item
    data_stripped = data_item.strip()
    data_stripped = re.sub(r"(\s\s+)", r" ", data_stripped)
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
    for index, rowdict in data_dict.items():
        data_item = rowdict[target_column]
        data_item, changes = basic_normalize(data_item, index)
        char_change_dict[index] = changes
        invalid_chars = identify_invalid_chars(data_item)
        rowdict["char_validation"] = tk.validate(invalid_chars, "string")
        if tk.validate(invalid_chars, "boolean"):
            rowdict[f"char_normalized_{target_column}"] = data_item
        else:
            for char in invalid_chars:
                source, location = tk.lookup(char, review_dict, reference_dict, "char")
                if source == "reference":
                    data_item = take_action(reference_dict,
                                            char,
                                            data_item,
                                            location)
                    if reference_dict[location]["allow"] != "":
                        allowed_chars.add(char)
                elif source == "review":
                    if data_item not in review_dict[location]["context"]:
                        if len(review_dict[location]["context"]) < 300:
                            context_string = review_dict[location]["context"]
                            context_string += f""", '{data_item}'"""
                            occurrences = review_dict[location]["occurrences"]
                            occurrences += 1
                            review_dict[location]["occurrences"] = occurrences
                            review_dict[location]["context"] = context_string
                else:
                    id = tk.next_index(review_dict)
                    review_dict[id] = {}
                    review_dict[id]["index"] = id
                    review_dict[id]["invalid_character"] = char
                    review_dict[id]["context"] = f"""'{data_item}'"""
                    review_dict[id]["occurrences"] = 1
                    review_dict[id]["replace_with"] = ""
                    review_dict[id]["remove"] = ""
                    review_dict[id]["invalidate"] = ""
                    review_dict[id]["allow"] = ""
            invalid_chars = identify_invalid_chars(data_item)
            for char in invalid_chars.copy():
                if char in allowed_chars:
                    invalid_chars.remove(char)
            rowdict["char_validation"] = tk.validate(invalid_chars, "string")
            if tk.validate(invalid_chars, "boolean"):
                rowdict[f"char_normalized_{target_column}"] = data_item
            else:
                rowdict[f"char_normalized_{target_column}"] = "!"
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
