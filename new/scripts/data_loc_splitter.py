import re


def reindex_by_split(data_dict, target_column):
    split_index = 0
    new_data_dict = {}
    for unsplit_index, rowdict in data_dict.items():
        data_item = rowdict[target_column]
        if type(data_item) is str:
            new_data_dict[split_index] = {}
            new_data_dict[split_index]["index"] = split_index
            new_data_dict[split_index]["original_index"] = unsplit_index
            for key, value in rowdict.items():
                if key != "index":
                    new_data_dict[split_index][key] = value
            new_data_dict[split_index]["split_phrase"] = data_item
            split_index += 1
        elif type(data_item) is list:
            for item in data_item:
                new_data_dict[split_index] = {}
                new_data_dict[split_index]["index"] = split_index
                new_data_dict[split_index]["original_index"] = unsplit_index
                for key, value in rowdict.items():
                    if key != "index":
                        new_data_dict[split_index][key] = value
                new_data_dict[split_index]["split_phrase"] = item
                split_index += 1
    return new_data_dict


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


def split_data_loc(string):
    """
    Normalize localization phrases in a given text by identifying combined
    prefixes and types and associating numbers to these types across segments
    split by commas, semicolons, or "and". Both prefixes and types are dynamic.

    Args:
    string (str): Input text containing localization phrases that need
    normalization.

    Returns:
    list: A list of normalized localization phrases.
    """
    # Convert lists of prefixes and types into regex patterns, escaping each entry properly
    prefixes = ["extended data",
                "supplemental",
                "supporting",
                "additional",
                "extended"]
    types = ["data", "file", "figure", "table", "information", "page"]
    prefixes_pattern = r"(?:" + "|".join(re.escape(prefix) for prefix in prefixes) + r")\s+"
    types_pattern = "|".join(re.escape(type) for type in types)

    # Full pattern that optionally captures any prefix followed by any type
    full_types_pattern = r"(" + prefixes_pattern + r")?(" + types_pattern + r")"

    # Removes punctuation at the end of a string
    string = re.sub(r"(\.|,)+$", r"", string)

    # Normalizing the text by replacing all delimiters with ";"
    text = re.sub(r",|;| and ", ";", string)
    # Split the text using ";" and remove any empty segments or segments that contain only spaces
    segments = [segment.strip() for segment in text.split(";") if segment.strip()]

    results = []
    current_type = None

    for segment in segments:
        original_segment = segment.strip()

        # Special check for superfluous version tags and remove them
        if re.search(r"\(v\d+(\.\d+)?\)", original_segment):
            segment = re.sub(r"\(v\d+(\.\d+)?\)", "", original_segment).strip()

        # Check for hanging periods leftover from abbreviations and remove them
        if re.search(r"\. ", segment):
            segment = re.sub(r"\. ", " ", segment)

        # Special check for "text p#|text p #|text p #" and replace with "page #"
        pattern = r"text p\.?\s*(\d+)"
        replacement = r"page \1"
        if re.search(pattern, segment):
            segment = re.sub(pattern, replacement, segment)

        # Fit PDB identifiers with the correct prefix, ensuring at least one letter in the sequence
        pattern = r"\b(pdb[: ]\s*)?([0-9][a-zA-Z0-9]{2}[a-zA-Z]|[0-9][a-zA-Z0-9][a-zA-Z][a-zA-Z0-9]|[0-9][a-zA-Z][a-zA-Z0-9]{2})\b"

        def replace(match):
            # Return formatted string with "pdb " followed by the identifier
            return f"pdb {match.group(2)}"
        # Replace the segment using the custom replace function
        if re.search(pattern, segment):
            segment = re.sub(pattern, replace, segment)

        # Detect the presence of a full type (prefix + type) and capture it
        type_match = re.search(full_types_pattern, segment, re.IGNORECASE)
        if type_match:
            prefix = type_match.group(1) or ""
            type = type_match.group(2)
            current_type = f"{prefix}{type}".strip()

        # After identifying the type, extract all numbers from the segment
        numbers = re.findall(r"\bs?\d+[a-zA-Z]?(?:&[a-zA-Z])*\b", segment)
        for number in numbers:
            if "&" in number:
                base_number = re.match(r"s?\d+", number).group(0)
                parts = re.split(r"&", number)
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
            # if original_segment == segment:
            #    segment = f"UNNORMALIZED: {segment}"
            results.append(segment)

    # Testing checks for acceptable "x and y" cases (e.g. "materials and methods")
    results = approved_and_phrases(results)

    return results