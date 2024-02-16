import sys
import re
from converter import TSV2dict, dict2TSV


def numberize(numstring):
    """
    Converts a string form of a number with or without a decimal into an int
    or a float depending on the presence of a decimal.

    -- numstring: The string, e.g., "3.5" or "14", to be converted.
    -- return: An int or a float, e.g., 3.5 or 14.
    """
    if "." in numstring:
        number = float(numstring)
    else:
        number = int(numstring)
    return number


def calculate_confidence(rowdict):
    confidence = 70
    numberfields = [
        "exact_age",
        "minimum_age",
        "maximum_age",
        "mean_age",
        "median_age",
    ]
    confidence_by_type = {
        "range": 1,
        "exact": 1.1,
        "null": 1.5,
        "manual": 0.7,
        "description": 1,
        "mean": 1.1,
        "bounded": 1,
        "range_with_mean": 0.9,
    }
    known_units = [
        "year",
        "month",
        "week",
        "day",
        "hour",
    ]
    for field in numberfields:
        if rowdict[field] != "":
            m = re.search(r"[a-zA-Z]", rowdict[field])
            if m:
                confidence = confidence * 0.4
    if confidence == 75:
        if rowdict["minimum_age"] != "" and rowdict["maximum_age"] != "":
            min = numberize(rowdict["minimum_age"])
            max = numberize(rowdict["maximum_age"])
            if min >= max:
                confidence = confidence * 0.3
            else:
                confidence = confidence * 1.2
    type_confidence = confidence_by_type[rowdict["age_data_type"]]
    confidence = confidence * type_confidence
    if "!" in rowdict["age_description"]:
        confidence = confidence * 0.1
    if rowdict["unit"] != "":
        if rowdict["unit"] in known_units:
            confidence = confidence * 1.1
        else:
            confidence = confidence * 0.2
    if confidence > 100:
        confidence = 99.9
    rowdict["confidence%"] = confidence
    return rowdict


if __name__ == "__main__":
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    maindict = TSV2dict(input_path)
    for index, rowdict in maindict.items():
        rowdict = calculate_confidence(rowdict)
    dict2TSV(maindict, output_path)
