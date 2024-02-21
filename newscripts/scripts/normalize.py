import csv
import sys
import re
import unicodedata as ud
from converter import TSV2dict, dict2TSV
from formatter import format_age


def prepare_spellcheck(spellcheckTSV):
    """
    Creates SCdict, in which keys are preferred spellings or representations
    of particular words and values are lists of  alternative or incorrect forms
    of those words, e.g., SCdict["years"] = ["yeras", "yesrs"] to be used for
    spellchecking.

    -- spellcheckTSV: The source TSV that contains a column for preferred terms
       and a column for alternative terms.
    -- return: SCdict.
    """
    with open(spellcheckTSV, "r", encoding="UTF-8") as infile:
        reader = csv.DictReader(infile, delimiter="\t")
        SCdict = {}
        for row in reader:
            correctTerm = str(row["correct_term"])
            variants = str(row["variants_to_replace"])
            variants = variants.split("|")
            SCdict[correctTerm] = variants
    sc_data_dict = {}
    for preferred, alternative_list in SCdict.items():
        for alternative in alternative_list:
            sc_data_dict[alternative] = {
                "variant_term": alternative,
                "preferred_term": preferred,
                "occurrences": 0,
            }
    return SCdict, sc_data_dict


def run_spellcheck(string, SCdict, sc_data_dict):
    """
    Spellchecks using SCdict (created via prepare_spellcheck(spellcheckTSV) and
    used to store preferred and alternative versions of certain words.

    -- string: The text to be spellchecked.
    -- SCdict: The spellcheck dict.
    -- sc_data_dict: Dict that stores usage frequencies of each term in the
       spellcheck dict.
    -- return: A corrected version of the string.
    """
    # Checks for each alternative term in each preferred-alternative term
    # pair in SCdict, then replaces alternatives with preferred terms.
    # Recognizes terms divided by whitespace, hyphens, periods, or commas,
    # but not alphanumeric characters, i.e., would catch "one" in the
    # string "three-to-one odds", but not "one" in "bone."
    for preferred, alternatives in SCdict.items():
        for alternative in alternatives:
            if alternative in string:
                string = re.sub(
                    fr"(^|\s+|[-.,]+)({alternative})($|\s+|[-.,]+)",
                    fr"\g<1>{preferred}\g<3>",
                    string
                )
                count = sc_data_dict[alternative]["occurrences"]
                count += 1
                sc_data_dict[alternative]["occurrences"] = count
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


def output_spellcheck_data(sc_data_dict):
    """
    Logs frequency data for spellcheck replacements in spellcheck_data.tsv.
    """
    with open("spellcheck_data.tsv", "w", newline="\n") as tsvfile:
        fieldnames = ["variant_term", "preferred_term", "occurrences"]
        writer = csv.DictWriter(tsvfile, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for term, data in sc_data_dict.items():
            writer.writerow(
                {
                    "variant_term": term,
                    "preferred_term": data["preferred_term"],
                    "occurrences": data["occurrences"]
                })


def normalize(inputTSV, outputTSV, spellcheckTSV, target_column, style):
    """
    Applies normalization steps to all data items in target column or columns
    in an input TSV, creates a new column for the normalized data, and writes
    updated TSV to an output path.

    -- inputTSV: Path of TSV to be normalized.
    -- outputTSV: Path of TSV with new normalized data.
    -- spellcheckTSV: Path of TSV with preferred-alternative term pairs for
       data spellchecking.
    -- target_column: A string or list. If string, the name of the column to
       be normalized. If list, the names of the columns to be normalized.
    -- style: A style (e.g. age) to be applied via formatter. Currently
       anything other than "age" in this argument place will result in no
       style being applied.
    """
    # Make spellcheck dict.
    SCdict, sc_data_dict = prepare_spellcheck(spellcheckTSV)
    # Make dict of TSV data.
    maindict = TSV2dict(inputTSV)
    for index, rowdict in maindict.items():
        # If multiple columns to standardize, do all in list.
        if type(target_column) == list:
            for column in target_column:
                data = rowdict[column]
                standardized_data = standardize_string(data)
                sc_data = run_spellcheck(standardized_data, SCdict, sc_data_dict)
                newcolumn = f"normalized_{column}"
                rowdict[newcolumn] = sc_data
        # If only one column to standardize, do one.
        else:
            data = rowdict[target_column]
            standardized_data = standardize_string(data)
            sc_data = run_spellcheck(standardized_data, SCdict, sc_data_dict)
            newcolumn = f"normalized_{target_column}"
            rowdict[newcolumn] = sc_data
    if style == "age":
        maindict = format_age(maindict, newcolumn)
    output_spellcheck_data(sc_data_dict)
    dict2TSV(maindict, outputTSV)


if __name__ == "__main__":
    inputTSV = sys.argv[1]
    outputTSV = sys.argv[2]
    spellcheckTSV = sys.argv[3]
    target_column = sys.argv[4]
    style = sys.argv[5]
    normalize(inputTSV, outputTSV, spellcheckTSV, target_column, style)