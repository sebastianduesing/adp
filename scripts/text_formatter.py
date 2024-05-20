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
    # Split the text using ';' and remove any empty segments or segments that contain only spaces
    segments = [segment.strip() for segment in text.split(';') if segment.strip()]
    
    results = []
    current_type = None

    for segment in segments:
        segment = segment.strip()
        
        # Special check for "text p.#|text p. #|text p #" and replace with "page #"
        pattern = r'text p\.?\s*(\d+)'
        replacement = r'page \1'
        if re.search(pattern, segment):
            segment = re.sub(pattern, replacement, segment)
        
        # Special check for superfluous version tags and remove them
        if re.search(r'\(v\d+(\.\d+)?\)', segment):
            segment = re.sub(r'\(v\d+(\.\d+)?\)', '', segment)[:-1]
                
        # Detect the presence of a type and capture it with any leading words as prefix
        type_match = re.search(r'(\b\w+\s)?(figure|table|page)\b', segment, re.IGNORECASE)
        if type_match:
            prefix = type_match.group(1) or ""
            current_type = f"{prefix.strip()} {type_match.group(2)}".strip()
       
        # After identifying the type, extract all numbers from the segment
        numbers = re.findall(r'\bs?\d+[a-zA-Z]?(?:&[a-zA-Z])*\b', segment)
        for number in numbers:
            # Check if '&' is present and iterate over each component
            if '&' in number:
                # Extract the base number part (digits and optional 's')
                base_number = re.match(r's?\d+', number).group(0)
                # Split on '&' and reconstruct each part with the base number
                parts = re.split(r'&', number)
                for i, part in enumerate(parts):
                    if i == 0:
                        # First part already includes the full initial part, just append it
                        results.append(f"{current_type} {part}")
                    else:
                        # Subsequent parts need the base number appended
                        results.append(f"{current_type} {base_number}{part}")
            else:
                # No '&' in the string, append directly
                results.append(f"{current_type} {number}")
        
        # TODO: The logic below is where text "slips through" our checks
        
        # If no numbers are found but a type is defined in the segment, treat as type element
        # However "figure" without a number is not useful
        if not numbers and type_match:
            results.append(segment)
        
        # If no numbers are found and no type is defined in the segment, treat as non-type element
        if not numbers and not type_match:
            results.append(segment)

    return results