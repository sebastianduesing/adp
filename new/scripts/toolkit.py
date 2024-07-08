import re


def normalize_whitespace(string):
    """
    Apply basic whitespace normalization to a string.
    """
    string = string.strip()
    string = re.sub(r"(\s\s+)", r" ", string)
    return string


def check_action(rowdict):
    """
    Check whether the user has specified an action to be taken in review file.

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


def clean_occurrences(review_dict):
    """
    Reset occurrences in review_dict to 1 to recoun each time script is rerun.
    """
    if len(review_dict.keys()) != 0:
        for index, rowdict in review_dict.items():
            rowdict["occurrences"] = 0
    return review_dict


def create_new_review_entry(review_dict, style, stage, id, invalid_item, data_item):
    """
    Create a new line item in the review sheet.
    """
    entry_dict = {}
    if stage == "char":
        stage = "character"
    entry_dict["index"] = id
    entry_dict[f"invalid_{stage}"] = invalid_item
    if style == "data_loc" and stage == "word":
        pdb = re.fullmatch(r"[0-9][0-9a-z]{3}", invalid_item)
        if pdb:
            entry_dict["pdb_plausible?"] = "Y"
        else:
            entry_dict["pdb_plausible?"] = "N"
    entry_dict["context"] = f"""'{data_item}'"""
    entry_dict["occurrences"] = 1
    entry_dict["replace_with"] = ""
    entry_dict["remove"] = ""
    entry_dict["invalidate"] = ""
    entry_dict["allow"] = ""
    return entry_dict


def add_to_review_entry(review_dict, location, data_item):
    """
    Update review dict line item with additional occurrences/context.
    """
    if data_item not in review_dict[location]["context"]:
        if len(review_dict[location]["context"]) < 300:
            context_string = review_dict[location]["context"]
            context_string += f""", '{data_item}'"""
            review_dict[location]["context"] = context_string
    occurrences = int(review_dict[location]["occurrences"])
    occurrences += 1
    review_dict[location]["occurrences"] = occurrences
    return review_dict



def next_index(dict_with_index):
    """
    Find next available index in a dict and returns it.
    """
    if len(dict_with_index.keys()) == 0:
        return 0
    else:
        indices = [int(i) for i in dict_with_index.keys()]
        test_index = 0
        while test_index in indices:
            test_index += 1
        return test_index


def lookup(invalid_item, review_dict, reference_dict, mode):
    """
    Finds index of a character if it is logged in either reference or review.
    """
    if mode == "char":
        mode = "character"
    source, location = None, None
    for index, rowdict in reference_dict.items():
        if invalid_item == rowdict[f"invalid_{mode}"]:
            source, location = "reference", index
            break
    if source is None:
        for index, rowdict in review_dict.items():
            if invalid_item == rowdict[f"invalid_{mode}"]:
                source, location = "review", index
                break
    return source, location


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
            new_index = next_index(reference_dict)
            row = review_dict[index].copy()
            row["index"] = new_index
            reference_dict[new_index] = row
            del review_dict[index]
    return review_dict, reference_dict


def validate(invalid_set, mode):
    """
    Return an indicator about whether a string contains only valid items.

    Validation passes if there is nothing in invalid_set.
    Passing indicator = True if mode is "boolean", "pass" otherwise.
    Failing indicator = False if mode is "boolean", "fail" otherwise.
    """
    if len(invalid_set) == 0:
        if mode == "boolean":
            return True
        else:
            return "pass"
    else:
        if mode == "boolean":
            return False
        else:
            return "fail"



