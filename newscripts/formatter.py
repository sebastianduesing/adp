import re


def age_style(string):
    """
    Removes extraneous hyphens in age data, e.g.,
    1-year-old --> 1 year old
    1 year-old --> 1 year old
    1-year old --> 1 year old
    4-6 year-old --> 4-6 year old

    Removes "old", e.g.,
    1 year old --> 1 year
    1-2 day old --> 1-2 day

    -- string: The string to be processed.
    -- return: The processed version of the string.
    """
    string = re.sub(
        r"(\d+\.?\d*)(-)(year|month|week|day|hour)",
        r"\g<1> \g<3>",
        string
    )
    string = re.sub(
        r"(year|month|week|day|hour)([\s-])(old)",
        r"\g<1>",
        string
    )
    return string


def format_age(age_dict, target_column):
    """
    Applies age data normalization steps to data in a column of age_dict.

    -- age_dict: A dict of age data created using converter.py.
    -- target_column: The column to be processed.
    -- return: A dict with a new column for age-formatted data.
    """
    new_column = f"{target_column}_style=age"
    for index, rowdict in age_dict.items():
        data = rowdict[target_column]
        age_formatted_data = age_style(data)
        rowdict[new_column] = age_formatted_data
    return age_dict
