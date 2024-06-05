import re


def approved_and_phrases(query_string_list):
    # Define the lists of approved phrases
    materials_list = ["material", "materials"]
    methods_list = ["method", "methods"]
    
    # Iterate through the query list checking for consecutive matches
    for i in range(len(query_string_list) - 1):
        # Check if current and next elements are in different sets
        if (query_string_list[i] in materials_list and query_string_list[i + 1] in methods_list) or \
           (query_string_list[i] in methods_list and query_string_list[i + 1] in materials_list):
            query_string_list[i] = "materials and methods"
            query_string_list.pop(i + 1)
            return query_string_list
    
    return query_string_list


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
    Normalize localization phrases in a given text by identifying combined prefixes and types
    and associating numbers to these types across segments split by commas, semicolons, or 'and'.
    Both prefixes and types are dynamic.

    Args:
    string (str): Input text containing localization phrases that need normalization.

    Returns:
    list: A list of normalized localization phrases.
    """
    # Convert lists of prefixes and types into regex patterns, escaping each entry properly
    prefixes = ['extended data', 'supplemental', 'supporting', 'additional', 'extended']
    types = ['data', 'file', 'figure', 'table', 'information', 'page']
    prefixes_pattern = r'(?:' + '|'.join(re.escape(prefix) for prefix in prefixes) + r')\s+'
    types_pattern = '|'.join(re.escape(type) for type in types)

    # Full pattern that optionally captures any prefix followed by any type
    full_types_pattern = r'(' + prefixes_pattern + r')?(' + types_pattern + r')'

    # Removes punctuation at the end of a string
    string = re.sub(r"(\.|,)+$", r"", string)
    
    # Normalizing the text by replacing all delimiters with ';'
    text = re.sub(r',|;| and ', ';', string)
    # Split the text using ';' and remove any empty segments or segments that contain only spaces
    segments = [segment.strip() for segment in text.split(';') if segment.strip()]

    results = []
    current_type = None

    for segment in segments:
        original_segment = segment.strip()
        
        # Special check for superfluous version tags and remove them
        if re.search(r'\(v\d+(\.\d+)?\)', original_segment):
            segment = re.sub(r'\(v\d+(\.\d+)?\)', '', original_segment).strip()
            
        # Check for hanging periods leftover from abbreviations and remove them
        if re.search(r'\. ', segment):
            segment = re.sub(r'\. ', ' ', segment)
        
        # Special check for "text p#|text p #|text p #" and replace with "page #"
        pattern = r'text p\.?\s*(\d+)'
        replacement = r'page \1'
        if re.search(pattern, segment):
            segment = re.sub(pattern, replacement, segment)
        
        # Detect the presence of a full type (prefix + type) and capture it
        type_match = re.search(full_types_pattern, segment, re.IGNORECASE)
        if type_match:
            prefix = type_match.group(1) or ""
            type = type_match.group(2)
            current_type = f"{prefix}{type}".strip()
       
        # After identifying the type, extract all numbers from the segment
        numbers = re.findall(r'\bs?\d+[a-zA-Z]?(?:&[a-zA-Z])*\b', segment)
        for number in numbers:
            if '&' in number:
                base_number = re.match(r's?\d+', number).group(0)
                parts = re.split(r'&', number)
                for i, part in enumerate(parts):
                    results.append(f"{current_type} {base_number}{part}" if i != 0 else f"{current_type} {part}")
            elif current_type:
                results.append(f"{current_type} {number}")
            else:
                results.append(number)
        
        # If no numbers are found but a type is defined in the segment, treat as type element
        if not numbers and type_match:
            results.append(segment)
        
        # If no numbers are found and no type is defined in the segment, treat as non-type element
        if not numbers and not type_match:
            # TODO: Decide if we want to keep the "UNNORMALIZED" tag
            #if original_segment == segment:
            #    segment = f"UNNORMALIZED: {segment}"
            results.append(segment)
            
    # Testing checks for acceptable "x and y" cases (e.g. "materials and methods")
    results = approved_and_phrases(results)

    return results

"""
input_strings = [
    "abstract and pdb 3gjf and 3hae",
    "tables 3, 6 and figure 4",
    "materials and methods, figure 1, table 2, and figure 3",
    "methods and materials",
    "table 3, 4, figure 4, and materials and methods",
    "table 1, materials and methods and figure 2",
    "methods, figure 1, table 2, and figure 3",
    "materials, figure 2",
    "methods, figure 4, materials",
    "page 42"
]

for string in input_strings:
    result = data_loc_phrase_normalizer(string)
    print(result)
"""