import sys
import re
from converter import TSV2dict, dict2TSV


def increase_dict_value(dict, key):
    """
    For use with a dictionary that tracks counts as values. Adds 1 to the count
    associated with the input key.
    """
    count = dict[key]
    count += 1
    dict[key] = count

def numberize(string):
    """
    Converts a number in string form to int or float depending on whether it
    has a decimal point in it.
    """
    m = re.fullmatch(r"[0-9.]+", string)
    if not m:
        return None
    else:
        if "." in string:
            string = float(string)
        else:
            string = int(string)
        return string

def pull_apart_age(string, counter_dict):
    """
    Picks apart a free-text string expressing an age value into its components,
    e.g., separating "8-10 year" into the following:
    Minimum age = 8
    Maximum age = 10
    Unit = year

    -- string: The string to be processed.
    -- counter_dict: A dict that stores age types as keys and counts of
       occurrences of those types as values.
    -- return: A dict with column values to be fed into sort_age().
    """
    agedict = {}
    agedict["exact_age"] = ""
    agedict["minimum_age"] = ""
    agedict["maximum_age"] = ""
    agedict["mean_age"] = ""
    agedict["median_age"] = ""
    agedict["unit"] = ""
    agedict["age_description"] = ""
    agedict["age_data_type"] = ""

    # Finds numberless values.
    m = re.fullmatch(r"^\D*", string)
    if m:
        # Finds null values.
        n = re.fullmatch(r"null", string)
        if n:
            agedict["age_data_type"] = "null"
            increase_dict_value(counter_dict, "null")
        else:
            agedict["age_data_type"] = "description"
            agedict["age_description"] = string
            increase_dict_value(counter_dict, "description")

    # Finds values with an exact age, e.g., "1 year" or "27".
    m = re.fullmatch(r"(\d+\.?\d*)\s?(year|month|week|day|hour)*", string)
    if m:
        agedict["exact_age"] = m.group(1)
        agedict["unit"] = m.group(2)
        agedict["age_data_type"] = "exact"
        increase_dict_value(counter_dict, "exact")

    # Finds values with an age range, e.g., "3-5 year" or "2.3-12.4".
    m = re.fullmatch(r"(\d+\.?\d*)-(\d+\.?\d*)\s?(year|month|week|day|hour)*", string)
    if m:
        agedict["minimum_age"] = m.group(1)
        agedict["maximum_age"] = m.group(2)
        agedict["unit"] = m.group(3)
        agedict["age_data_type"] = "range"
        increase_dict_value(counter_dict, "range")

    # Finds values bounded by a minimum or maximum, e.g., ">3 year".
    m = re.fullmatch(r"(<|>)(\d+\.?\d*)\s?(year|month|week|day|hour)*", string)
    if m:
        agedict["unit"] = m.group(3)
        agedict["age_data_type"] = "bounded"
        if "<" in string:
            agedict["maximum_age"] = m.group(2)
        else:
            agedict["minimum_age"] = m.group(2)
        increase_dict_value(counter_dict, "bounded")

    # Finds mean/average values, e.g., "mean age 30 year".
    m = re.fullmatch(r"(average|mean)([a-z:=.,\s]*)(\d+\.?\d*)\s?(year|month|week|day|hour)*", string)
    if m:
        agedict["mean_age"] = m.group(3)
        agedict["unit"] = m.group(4)
        agedict["age_data_type"] = "mean"
        increase_dict_value(counter_dict, "mean")

    # Finds +/- values, e.g., "28 +/- 10 year"
    m = re.fullmatch(r"(mean|average)?([a-z\s]*)(\d+\.?\d*) \+/- (\d+\.?\d*)\s?(year|month|week|day|hour)*", string)
    if m:
        base = numberize(m.group(3))
        variance = numberize(m.group(4))
        min = base-variance
        max = base+variance
        agedict["minimum_age"] = min
        agedict["maximum_age"] = max
        if "mean" in string or "average" in string:
            agedict["mean_age"] = m.group(3)
            agedict["age_data_type"] = "range_with_mean"
            increase_dict_value(counter_dict, "range_with_mean")
        else:
            agedict["age_data_type"] = "range"
            increase_dict_value(counter_dict, "range")
    return agedict


def sort_age(inputTSV, outputTSV, target_column):
    """
    Sorts parts of age data in columns into their own columns for minimum,
    maximum, unit, etc.

    -- inputTSV: The TSV to be processed.
    -- outputTSV: The TSV that will be created with the additional columns.
    -- target_column: The column to process.
    """
    maindict = TSV2dict(inputTSV)
    linecount = len(maindict.keys())
    counter_dict = {
        "bounded": 0,
        "description": 0,
        "exact": 0,
        "mean": 0,
        "range": 0,
        "range_with_mean": 0,
        "null": 0,
    }
    for index, rowdict in maindict.items():
        data = rowdict[target_column]
        age = pull_apart_age(data, counter_dict)
        for key, value in age.items():
            rowdict[key] = value
    all_types_count = 0
    for count in counter_dict.values():
        all_types_count += count
    total_percent = round((all_types_count/linecount)*100, 2)
    unsorted_count = linecount - all_types_count
    unsorted_percent = round((unsorted_count/linecount)*100, 2)
    print(f"\nSorted {all_types_count} age data items ({total_percent}% of all lines):\n")
    for type, count in counter_dict.items():
        percent = round((count/linecount)*100, 2)
        print(f"\t{count} {type} values sorted ({percent}% of all lines).")
    print(f"\nSorting complete. {unsorted_count} values unsorted ({unsorted_percent}% of all lines).\n")
    dict2TSV(maindict, "sorted_age.tsv")


if __name__ == "__main__":
    inputTSV = sys.argv[1]
    outputTSV = sys.argv[2]
    target_column = sys.argv[3]
    sort_age(inputTSV, outputTSV, target_column)
