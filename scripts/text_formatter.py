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
    Normalize localization phrases in a given text by identifying types ('figure', 'table', 'page')
    and associating numbers to these types across segments split by commas, semicolons, or 'and'.

    Args:
    text (str): Input text containing localization phrases that need normalization.

    Returns:
    list: A list of normalized localization phrases.
    """
    # Removes punctuation at the end of a string.
    string = re.sub(
        r"(\.|,)+$",
        r"",
        string
    )
    
    # Normalizing the text by replacing all delimiters with ';'
    text = re.sub(r',|;| and ', ';', string)
    # Split the text using ';'
    segments = text.split(';')
    
    results = []
    current_type = None

    for segment in segments:
        segment = segment.strip()
        
        # Special check for "text p.#" and replace with "page #"
        if re.search(r'text p\.\d+', segment):
            segment = re.sub(r'text p\.(\d+)', r'page \1', segment)
        
        # Special check for superfluous version tags and remove them
        if re.search(r'\(v\d+(\.\d+)?\)', segment):
            segment = re.sub(r'\(v\d+(\.\d+)?\)', '', segment)[:-1]
                
        # Detect the presence of a type and capture it with any leading words as prefix
        type_match = re.search(r'(\b\w+\s)?(figure|table|page)\b', segment, re.IGNORECASE)
        if type_match:
            prefix = type_match.group(1) or ""
            current_type = f"{prefix.strip()} {type_match.group(2)}".strip()
       
        # After identifying the type, extract all numbers
        numbers = re.findall(r'\bs?\d+\b', segment)
        for number in numbers:
            results.append(f"{current_type} {number}")
        
        # If no numbers are found and no type is defined in the segment, treat as non-type element
        if not numbers and not type_match:
            results.append(segment)

    return results