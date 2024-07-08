import re


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



