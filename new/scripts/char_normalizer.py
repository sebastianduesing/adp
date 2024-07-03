import os
import re
import sys
from converter import TSV2dict, dict2TSV


approved_chars = r"[a-zA-Z\d ,.+/<>()-]"


def identify_invalid_chars(string):
    """
    Returns a set of invalid characters found in input string.
    """
    invalid_chars = set()
    for char in string:
        m = re.fullmatch(approved_chars, char)
        if not m:
            invalid_chars.add(char)
    return invalid_chars


def validate(invalid_char_set, mode):
    """
    Returns an indicator about whether a string contains only valid chars.

    Validation passes if there is nothing in invalid_char_set.
    Passing indicator = True if mode is "boolean", "pass" otherwise.
    Failing indicator = False if mode is "boolean", "fail" otherwise.
    """
    if len(invalid_char_set) == 0:
        if mode == "boolean":
            return True
        else:
            return "pass"
    else:
        if mode == "boolean":
            return False
        else:
            return "fail"


def check_action(rowdict):
    """
    Checks whether the user has specified an action to be taken in review file.

    Examines one row in the review file.
    Returns action name if the user has done exactly one of the following:
    indicated a character to replace the target character with, marked that
    character for removal, marked that character as invalidating the string, or
    designated that character as allowable.
    Returns False otherwise.
    """
    actions = [
        rowdict["replace_with"] != "",
        rowdict["remove"] != "",
        rowdict["invalidate"] != "",
        rowdict["allow"] != ""
    ]
    truth_value = 0
    for action in actions:
        if action:
            truth_value += 1
    if truth_value == 1:
        for action in ["replace_with", "remove", "invalidate", "allow"]:
            if rowdict[action] != "":
                return action
    else:
        return None


def update_reference(review_dict, reference_dict):
    """
    Moves review_dict rows in which an action has been taken to reference_dict.
    """
    if len(review_dict.keys()) != 0:
        indices_to_transfer = []
        for index, rowdict in review_dict.items():
            if check_action(rowdict) is not None:
                indices_to_transfer.append(index)
        for index in indices_to_transfer:
            new_index = highest_index(reference_dict) + 1
            row = review_dict[index].copy()
            row["index"] = new_index
            reference_dict[new_index] = row
            del review_dict[index]
    return review_dict, reference_dict


def lookup(invalid_char, review_dict, reference_dict):
    """
    Finds index of a character if it is logged in either reference or review.
    """
    source, location = None, None
    for index, rowdict in reference_dict.items():
        if invalid_char == rowdict["invalid_character"]:
            source, location = "reference", index
            break
    if source is None:
        for index, rowdict in review_dict.items():
            if invalid_char == rowdict["invalid_character"]:
                source, location = "review", index
                break
    return source, location


def take_action(reference_dict, invalid_char, data_item, index):
    """
    Alters data_item as specified in reference_dict.
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


def highest_index(dict_with_index):
    """
    Finds highest index in a dict and returns it.
    """
    if len(dict_with_index.keys()) == 0:
        return -1
    else:
        indices = [int(i) for i in dict_with_index.keys()]
        return max(indices)


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
    review_dict, reference_dict = update_reference(review_dict, reference_dict)
    for index, rowdict in data_dict.items():
        data_item = rowdict[target_column]
        data_item, changes = basic_normalize(data_item, index)
        char_change_dict[index] = changes
        invalid_chars = identify_invalid_chars(data_item)
        rowdict["char_validation"] = validate(invalid_chars, "string")
        if validate(invalid_chars, "boolean"):
            rowdict[f"char_normalized_{target_column}"] = data_item
        else:
            for char in invalid_chars:
                source, location = lookup(char, review_dict, reference_dict)
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
                            review_dict[location]["context"] = context_string
                else:
                    id = highest_index(review_dict) + 1
                    review_dict[id] = {}
                    review_dict[id]["index"] = id
                    review_dict[id]["invalid_character"] = char
                    review_dict[id]["context"] = f"""'{data_item}'"""
                    review_dict[id]["replace_with"] = ""
                    review_dict[id]["remove"] = ""
                    review_dict[id]["invalidate"] = ""
                    review_dict[id]["allow"] = ""
            invalid_chars = identify_invalid_chars(data_item)
            for char in invalid_chars.copy():
                if char in allowed_chars:
                    invalid_chars.remove(char)
            rowdict["char_validation"] = validate(invalid_chars, "string")
            if validate(invalid_chars, "boolean"):
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
