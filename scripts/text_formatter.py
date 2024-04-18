import re


def age_phrase_normalizer(string):
    """
    Removes extraneous hyphens in age data, e.g.,
    1-year-old --> 1 year old
    1 year-old --> 1 year old
    1-year old --> 1 year old
    4-6 year-old --> 4-6 year old

    Removes "old", e.g.,
    1 year old --> 1 year
    1-2 day old --> 1-2 day

    Adjust punctuation and spacing.

    -- string: The string to be processed.
    -- return: The processed version of the string.
    """
    # Removes hyphenization between numbers and units.
    string = re.sub(
        r"(\d+\.?\d*)(-)(year|month|week|day|hour)",
        r"\g<1> \g<3>",
        string
    )
    # Standardizes spacing of +/- values.
    string = re.sub(
        r"(\d+\.?\d*)\s*(\+\/-)\s*(\d+\.?\d*)",
        r"\g<1> \g<2> \g<3>",
        string
    )
    # Standardizes spacing of ranges.
    string = re.sub(
        r"(\d+\.?\d*)\s*-\s*(\d+\.?\d*)",
        r"\g<1>-\g<2>",
        string
    )
    # Normalizes "[unit]s old" to "[unit]".
    string = re.sub(
        r"(\s|-)+(year|month|week|day|hour)([\s-]+)(old)",
        r" \g<2>",
        string
    )
    # Changes "less than" and "fewer than" to <.
    string = re.sub(
        r"less than|fewer than",
        r"<",
        string
    )
    # Changes "greater than" and "more than" to >.
    string = re.sub(
        r"greater than|more than",
        r">",
        string
    )
    # Removes spacing between > or < and digits.
    string = re.sub(
        r"(<|>) (\d)",
        r"\g<1>\g<2>",
        string
    )
    string = re.sub(
        r"(\d)\s+-\s+(\d)",
        r"\g<1>-\g<2>",
        string
    )
    # Removes punctuation at the end of a string.
    string = re.sub(
        r"(\.|,)+$",
        r"",
        string
    )
    # Changes "x to y" to "x-y".
    string = re.sub(
        r"(\d)(\s|-)+(to)(\s|-)+(\d)",
        r"\g<1>-\g<5>",
        string
    )
    return string

def data_loc_phrase_normalizer(string):
    """
    TODO: Add all additional normalizations for data location strings.
    
    Normalize a "data location" string according to domain-specific guidelines.

    This function takes a string representing a "data location" and performs
    domain-specific normalization techniques to render the string standardized
    and normalized according to the data location field guidelines.

    Parameters:
    string (str): The input string representing a "data location".

    Returns:
    str: The normalized and standardized version of the input string.

    """
    # Removes punctuation at the end of a string.
    string = re.sub(
        r"(\.|,)+$",
        r"",
        string
    )
    return string