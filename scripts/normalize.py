import csv
import sys
import re
import editdistance
import os.path
import unicodedata as ud
import pandas as pd
from converter import TSV2dict, dict2TSV
from text_formatter import age_phrase_normalizer, data_loc_phrase_normalizer


def is_known_invalid_location(data):
    # Checks if the string looks like a web URL
    if re.match(r'https?://\S+', data):
        return True
    # Checks if the string is composed only of numbers
    elif data.isdigit():
        return True
    # Checks if the string is an alphanumeric identifier without anything else
    elif re.match(r'^(?=.*[a-zA-Z])(?=.*[0-9])[a-zA-Z0-9]+$', data):
        return True
    # Checks if the string is a PDB identifier
    elif re.match(r'^pdb\s[a-zA-Z0-9]{4}$', data):
        return True
    # Checks if the string is a single letter followed by a number
    # TODO: Check what type of ID this is
    elif re.match(r'[a-zA-Z]\s\d+', data):
        return True
    return False


def academic_location_regex():
    # Base terms for figures and tables, including common abbreviations and supplementary materials
    fig_table_terms = r"\b(table|fig(?:ure)?|(supplementary|supplemental) (?:table|fig(?:ure)|data|file?)|supporting (?:table|fig(?:ure)|information?)|additional file(s)?|appendix|suppl)\b"
    # Sections of the paper
    sections = r"\b(title|abstract|introduction|materials and methods|animals and methods|materials|methods|results|discussion|conclusion|acknowledgements|references|appendices)\b"
    # Page terms to match different ways of referencing pages
    page_terms = r"((text )?page|pg\.?|p\.?) \d+"
    # Combine them with options for numbering (e.g., figure 1, table S1)
    pattern = rf"{fig_table_terms} (?:s)?\d+[a-z]?|{sections}|{page_terms}"

    return pattern


def biological_db_regex():
    # Handle PDB identifiers, generic identifiers (letter followed by numbers), and accession numbers
    pdb_pattern = r"\bpdb [a-zA-Z0-9]{4}\b"
    generic_identifier_pattern = r"\b[a-zA-Z] \d+\b"
    accession_pattern = r"\baccession(:)? [\w: ]+\b"
    return rf"({pdb_pattern})|({generic_identifier_pattern})|({accession_pattern})"


def website_url_regex():
    # Simple pattern for matching specific URLs and more generic HTTP URLs
    specific_domain = r"^https://hla-ligand-atlas\.org/[^\s]*$"
    general_http = r"^(https?://[^\s/$.?#].[^\s]*$)"
    return rf"({specific_domain})|({general_http})"


def is_normalized(string):
    academic_pattern = academic_location_regex()
    bio_db_pattern = biological_db_regex()
    website_pattern = website_url_regex()
        
    if re.search(academic_pattern, string, re.IGNORECASE):
        return 'Y'
    elif re.search(bio_db_pattern, string, re.IGNORECASE):
        return 'Y'
    elif re.search(website_pattern, string, re.IGNORECASE):
        return 'Y'
    else:
        return 'N'


def normalize_dataframe(df, column_name):
    # Explode the DataFrame to create a new row for each string in the list found in phrase_normalized_col
    df['normalized_location'] = df[column_name].copy()
    df = df.explode('normalized_location').reset_index(drop=True)
    df['normalized'] = df['normalized_location'].apply(is_normalized)
    return df

def dict_to_dataframe(maindict, column_name):
    # Convert dictionary to DataFrame
    df = pd.DataFrame.from_dict(maindict, orient='index')
    # Normalize data
    df = normalize_dataframe(df, column_name)
    return df

def dataframe_to_dict(df):
    # Convert DataFrame back to dictionary format suitable for dict2TSV
    result_dict = df.to_dict(orient='index')
    return result_dict


def prepare_spellcheck(spellcheckTSV, word_curation_TSV):
    """
    Creates SCdict, in which keys are preferred spellings or representations
    of particular words and values are lists of  alternative or incorrect forms
    of those words, e.g., SCdict["years"] = ["yeras", "yesrs"] to be used for
    spellchecking.
    Also creates WCdict, in which unknown words are pulled out for manual
    review and curation. Curated words in WCdict are used as references like
    terms in the spellcheck TSV.

    -- spellcheckTSV: The source TSV that contains a column for preferred terms
       and a column for alternative terms.
    -- return: SCdict.
    """
    with open(spellcheckTSV, "r", encoding="UTF-8") as infile:
        reader = csv.DictReader(infile, delimiter="\t")
        SCdict = {}
        for row in reader:
            correct_term = str(row["correct_term"])
            input_word = str(row["input_word"])
            input_context = str(row["input_context"])
            SCdict[input_word] = {
                "input_word": input_word,
                "correct_term": correct_term,
                "input_context": input_context,
            }
    with open(word_curation_TSV, "r", encoding="UTF-8") as infile:
        reader = csv.DictReader(infile, delimiter="\t")
        WCdict = {}
        for row in reader:
            correct_term = str(row["correct_term"])
            input_word = str(row["input_word"])
            input_context = str(row["input_context"])
            WCdict[input_word] = {
                "input_word": input_word,
                "correct_term": correct_term,
                "input_context": input_context,
            }
    for input_word, word_dict in WCdict.items():
        if word_dict["correct_term"] != "":
            if input_word not in SCdict.keys():
                SCdict[input_word] = word_dict
    sc_data_dict = {}
    for input_word, word_dict in SCdict.items():
        sc_data_dict[input_word] = {
            "input_word": input_word,
            "correct_term": word_dict["correct_term"],
            "occurrences": 0,
            }
    return SCdict, WCdict, sc_data_dict


def run_spellcheck(string, SCdict, WCdict,  sc_data_dict):
    """
    Spellchecks using SCdict (created via prepare_spellcheck(spellcheckTSV) and
    used to store preferred and alternative versions of certain words.

    -- string: The text to be spellchecked.
    -- SCdict: The spellcheck dict.
    -- WCdict: The manual word-curation dict.
    -- sc_data_dict: Dict that stores usage frequencies of each term in the
       spellcheck dict.
    -- return: A corrected version of the string.
    """
    # Checks for each alternative term in each preferred-alternative term
    # pair in SCdict, then replaces alternatives with preferred terms.
    # Recognizes terms divided by whitespace, hyphens, periods, or commas,
    # but not alphanumeric characters, i.e., would catch "one" in the
    # string "three-to-one odds", but not "one" in "bone."
    delimiters = [",", ".", "-", " ", "(", ")", ":", ";", "+", "=", ">", "<"]
    string_stripped = string
    for delimiter in delimiters:
        string_stripped = " ".join(string_stripped.split(delimiter))
        wordlist = string_stripped.split(" ")
    known_words = []
    for input_word, word_dict in SCdict.items():
        known_words.append(word_dict["correct_term"])
    for word in wordlist:
        if word in SCdict.keys():
            input_word = word
            correct_term = SCdict[input_word]["correct_term"]
            string = re.sub(
                fr"(^|\s+|[-.,]+)({input_word})($|\s+|[-.,]+)",
                fr"\g<1>{correct_term}\g<3>",
                string
            )
            count = sc_data_dict[input_word]["occurrences"]
            count += 1
            sc_data_dict[input_word]["occurrences"] = count
        elif word in known_words:
            continue
        elif word in WCdict.keys():
            continue
        elif re.fullmatch(r"[0-9=+\-/<>:]+", word):
            continue
        else:
            WCdict[word] = {
                "input_word": word,
                "correct_term": "",
                "input_context": string,
            }
    return string


def standardize_string(string):
    """
    Adapted from JasonPBennett/Data-Field-Standardization/.../data_loc_v2.py

    Standardizes a string by removing unnecessary whitespaces,
    converting to ASCII, and converting to lowercase.

    :param string: The string to be standardized.
    :return: Standardized string.
    """
    
    # Convert en- and em-dashes to hyphens.
    string = string.replace(r"–", "-")
    string = string.replace(r"—", "-")
    # Standardize plus-minus characters.
    string = string.replace(r"±", r"+/-")
    # Remove unnecessary whitespaces.
    string = string.strip()
    string = re.sub(r"(\s\s+)", r" ", string)
    # Convert to ascii.
    string = ud.normalize('NFKD', string).encode('ascii', 'ignore').decode('ascii')
    # Convert to lowercase.
    string = string.lower()
    return string


def output_spellcheck_data(sc_data_dict, WCdict, word_curation_TSV, target_column, style):
    """
    Logs frequency data for spellcheck replacements in <style>_spellcheck_data.tsv.
    Also logs unknown words stored in WCdict in word_curation_TSV.

    -- sc_data_dict: A dict of spellcheck data.
    -- WCdict: A dict of words to be manually curated.
    -- word_curation_TSV: Path to the TSV that stores word curation data.
    """
    with open(os.path.join(style, f"output_files/{target_column}_spellcheck_data.tsv"), "w", newline="\n") as tsvfile:
        fieldnames = ["input_word", "correct_term", "occurrences"]
        writer = csv.DictWriter(tsvfile, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for term, data in sc_data_dict.items():
            writer.writerow(
                {
                    "input_word": term,
                    "correct_term": data["correct_term"],
                    "occurrences": data["occurrences"]
                })
    with open(word_curation_TSV, "w", newline="\n") as tsvfile:
        fieldnames = ["input_word", "correct_term", "input_context"]
        writer = csv.DictWriter(tsvfile, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for term, data in WCdict.items():
            writer.writerow(
                {
                    "input_word": term,
                    "correct_term": data["correct_term"],
                    "input_context": data["input_context"]
                })


def normalize(inputTSV, outputTSV, spellcheckTSV, word_curation_TSV, target_column, style):
    """
    Applies normalization steps to all data items in target column or columns
    in an input TSV, creates a new column for the normalized data, and writes
    updated TSV to an output path.

    -- inputTSV: Path of TSV to be normalized.
    -- outputTSV: Path of TSV with new normalized data.
    -- spellcheckTSV: Path of TSV with preferred-alternative term pairs for
       data spellchecking.
    -- word_curation_TSV: Path of TSV where unknown words will be stored for
       manual review/curation.
    -- target_column: A string or list. If string, the name of the column to
       be normalized. If list, the names of the columns to be normalized.
    -- style: A style (e.g. age) to be applied via formatter. Currently
       anything other than "age" in this argument place will result in no
       style being applied.
    """
    SCdict, WCdict, sc_data_dict = prepare_spellcheck(spellcheckTSV, word_curation_TSV)
    maindict = TSV2dict(inputTSV)
    
    char_column = f"char_normalized_{target_column}"
    word_column = f"word_normalized_{target_column}"
    phrase_column = f"phrase_normalized_{target_column}"
    
    char_score_column = f"char_normalization_score_{target_column}"
    word_score_column = f"word_normalization_score_{target_column}"
    phrase_score_column = f"phrase_normalization_score_{target_column}"
    
    for index, rowdict in maindict.items():
        original_data = rowdict[target_column]
        data = standardize_string(original_data)

        rowdict[char_column] = data
        rowdict["char_normalized"] = "Y" if rowdict[char_column] != original_data else "N"
        rowdict[char_score_column] = editdistance.eval(original_data, data)
        
        sc_data = run_spellcheck(data, SCdict, WCdict, sc_data_dict)
        rowdict[word_column] = sc_data
        rowdict["word_normalized"] = "Y" if rowdict[word_column] != rowdict[char_column] else "N"
        rowdict[word_score_column] = editdistance.eval(rowdict[char_column], rowdict[word_column])
        
        if style == "age":
            rowdict[phrase_column] = age_phrase_normalizer(sc_data)
            # Simple check to see if the phrase was normalized
            rowdict[phrase_score_column] = editdistance.eval(sc_data, rowdict[phrase_column])
            rowdict["phrase_normalized"] = "Y" if rowdict[phrase_column] != rowdict[word_column] else "N"
        elif style == "data_loc":
            rowdict[phrase_column] = data_loc_phrase_normalizer(sc_data)
            # Because this is a list, extract first element to check if it was normalized
            rowdict[phrase_score_column] = editdistance.eval(sc_data, rowdict[phrase_column])
            if rowdict[phrase_column] and rowdict[word_column]:
                rowdict["phrase_normalized"] = "Y" if rowdict[phrase_column][0] != rowdict[word_column] else "N"
            # TODO: Hits this 31 times... why????
            # Some issue with specific phrases containing "and"
            else:
                print(f" -------- CURR INDEX: {index} -------- ")
                print(f"FOUND AT {word_column} in rowdict: {rowdict[word_column]}")
                print(f"FOUND AT {phrase_column} in rowdict: {rowdict[phrase_column]}")
                rowdict["phrase_normalized"] = "WTF"       
        else:
            print(f"Error: {style} is not a valid style.")
            sys.exit(1)
    
    # Output spellcheck data and unknown words for manual curation.        
    output_spellcheck_data(sc_data_dict, WCdict, word_curation_TSV, target_column, style)
    
    # Add additional columns to the TSV to finalize data location normalization.
    # TODO: Decide on this or go with inserted N/A values.
    if style == "data_loc":
        # Convert dict to DataFrame, normalize, and convert back
        df = dict_to_dataframe(maindict, phrase_column)
        final_dict = dataframe_to_dict(df)
    
    dict2TSV(final_dict, outputTSV)


if __name__ == "__main__":
    # Check style; also name of directory where TSVs are found/stored.
    style = sys.argv[6]
    # Create the paths for the input and output TSVs.
    inputTSV = os.path.join(style, sys.argv[1])
    outputTSV = os.path.join(style, sys.argv[2])
    spellcheckTSV = os.path.join(style, sys.argv[3])
    word_curation_TSV = os.path.join(style, sys.argv[4])
    target_column = sys.argv[5]
    # Verify that the files exist.
    file_paths = [inputTSV, spellcheckTSV, word_curation_TSV]
    for path in file_paths:
        if not os.path.isfile(path):
            print(f"Error: {path} does not exist.")
            sys.exit(1)
    normalize(inputTSV, outputTSV, spellcheckTSV, word_curation_TSV, target_column, style)