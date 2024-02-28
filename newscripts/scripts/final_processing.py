import sys
import re
from converter import TSV2dict, dict2TSV

def add_readable(rowdict):
    """
    Adds a column for a standardized human-readable age format based on sorted
    fields.

    rowdict: The dict of the row to which the column will be added.
    return: rowdict with the column "readable_age" added.
    """
    text = ""
    exact = rowdict["exact_age"]
    min = rowdict["minimum_age"]
    max = rowdict["maximum_age"]
    mean = rowdict["mean_age"]
    median = rowdict["median_age"]
    agelist = rowdict["age_list"]
    unit = rowdict["unit"]
    unit = f" {unit}" if unit != "" else ""
    description = rowdict["age_description"]
    if exact != "":
        text = f"{exact}{unit}"
    if min != "" and max != "":
        text = f"{min}-{max}{unit}"
    elif min != "":
        text = f">{min}{unit}"
    elif max != "":
        text = f">{max}{unit}"
    if mean != "" and text != "":
        text = f"{text} (mean = {mean}){unit}"
    elif mean != "":
        text = f"{mean}{unit} (mean)"
    if median != "" and text != "":
        text = f"{text} (median = {median}){unit}"
    elif median != "":
        text = f"{median}{unit} (median)"
    if text != "" and description != "":
        text = f"{text} ({description})"
    elif description != "":
        text = f"{description}"
    elif agelist != "":
        text = f"{agelist}{unit}"
    if text == "":
        text = "null"
    rowdict["readable_age"] = text
    return rowdict


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
    """
    Adds the column confidence%, a value approximating the degree to which the
    sorted data is trusted to accurately represent the input free-text data.
    The confidence value is based upon several factors, including the data type
    (e.g., range, null, exact), whether or not the columns containing numerical
    data have any unexpected alphabet characters, whether or not minimums are
    lower than maximums, whether or not a manual curation warning flag ("!") is
    present in the description column, and whether or not the text in the
    "unit" field matches known/expected units.

    -- rowdict: The dict of the row to which the column will be added.
    -- return: rowdict with the column confidence% added.
    """
    confidence = 60
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
        "null": 2,
        "manual": 0.8,
        "description": 1,
        "list": 1,
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
                confidence = confidence * 0.1
    if confidence == 60:
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
    rowdict["confidence_score"] = round(confidence, 1)
    return rowdict


if __name__ == "__main__":
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    maindict = TSV2dict(input_path)
    for index, rowdict in maindict.items():
        rowdict = add_readable(rowdict)
        rowdict = calculate_confidence(rowdict)
    dict2TSV(maindict, output_path)
