import csv
import re


def read_config(path):
    """
    Makes a dict from a config file that has columns for regexes to be matched
    and substitutions, for use with re.sub by apply_style().

    -- path: Path of the TSV config file.
    -- return: Dict with match patterns as keys and substitutions as values.
    """
    with open(path, "r", encoding="UTF-8") as infile:
        reader = csv.DictReader(infile, delimiter="\t")
        style_dict = {}
        for row in reader:
            style_dict["match_pattern"] = row["match_pattern"]
            style_dict["replacement"] = row["replacement"]
        print(f"{len(style_dict.keys())} lines read from config file.")
        return style_dict


def apply_style(age_dict, target_column, style_dict):
    """
    Applies age data normalization steps to data in a column of age_dict.

    -- age_dict: A dict of age data created using converter.py.
    -- target_column: The column to be processed.
    -- style_dict: A dict of patterns and substitutions, made by read_config().
    -- return: A dict with a new column for age-formatted data.
    """
    new_column = f"{target_column}_styled"
    for index, rowdict in age_dict.items():
        data = rowdict[target_column]
        for pattern, replacement in style_dict.items():
            data = re.sub(pattern, replacement, data)
        rowdict[new_column] = data
    return age_dict
