import csv
import sys
import re
import unicodedata as ud
from converter import TSV2dict, dict2TSV
from formatter import age_phrase_normalizer


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
    delimiters = [",", ".", "-", " ", "(", ")"]
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


def output_spellcheck_data(sc_data_dict, WCdict, word_curation_TSV):
    """
    Logs frequency data for spellcheck replacements in spellcheck_data.tsv.
    Also logs unknown words stored in WCdict in word_curation_TSV.

    -- sc_data_dict: A dict of spellcheck data.
    -- WCdict: A dict of words to be manually curated.
    -- word_curation_TSV: Path to the TSV that stores word curation data.
    """
    with open("spellcheck_data.tsv", "w", newline="\n") as tsvfile:
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

def output_normalization_data(maindict):
    """
    Outputs data on how many rows get normalized/formatted in 
    normalization_data.txt. Data is based on values in the columns
    "normalization_altered" and "formatting_altered".

    -- maindict: The dict from which the normalization data will be gathered.
    """
    linecount = len(maindict.keys())
    normalized_count = 0
    formatted_count = 0
    yes_norm_yes_form = 0
    yes_norm_no_form = 0
    no_norm_no_form = 0
    no_norm_yes_form = 0
    for index, rowdict in maindict.items():
        if rowdict["normalization_altered"] == "Y":
            normalized = True
        else:
            normalized = False
        if rowdict["formatting_altered"] == "Y":
            formatted = True
        else:
            formatted = False
        if normalized:
            normalized_count += 1
            if formatted:
                formatted_count += 1
                yes_norm_yes_form += 1
            else:
                yes_norm_no_form += 1
        elif formatted:
            no_norm_yes_form += 1
            formatted_count += 1
        else:
            no_norm_no_form += 1
    data = open("normalization_data.txt", "w")
    data.write(f"""ROWS AFFECTED BY NORMALIZATION/FORMATTING:

{normalized_count} ({round((normalized_count/linecount)*100,2)}%) lines normalized.
{formatted_count} ({round((formatted_count/linecount)*100,2)}%) lines formatted.

{no_norm_no_form} lines ({round((no_norm_no_form/linecount)*100,2)}%) were neither normalized nor formatted.
{yes_norm_yes_form} lines ({round((yes_norm_yes_form/linecount)*100,2)}%) were normalized and formatted.
{yes_norm_no_form} lines ({round((yes_norm_no_form/linecount)*100,2)}%) were normalized but not formatted.
{no_norm_yes_form} lines ({round((no_norm_yes_form/linecount)*100,2)}%) were not normalized but were formatted.""")
    print("Normalization data saved to normalization_data.txt.")


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
    # Make spellcheck dict.
    SCdict, WCdict, sc_data_dict = prepare_spellcheck(spellcheckTSV, word_curation_TSV)
    # Make dict of TSV data.
    maindict = TSV2dict(inputTSV)
    for index, rowdict in maindict.items():
        data = rowdict[target_column]
        standardized_data = standardize_string(data)
        charcolumn = f"char_normalized_{target_column}"
        rowdict[charcolumn] = standardized_data
        if rowdict[charcolumn] != rowdict[target_column]:
            rowdict["char_normalized"] = "Y"
        else:
            rowdict["char_normalized"] = "N"
        sc_data = run_spellcheck(standardized_data, SCdict, WCdict, sc_data_dict)
        wordcolumn = f"word_normalized_{target_column}"
        rowdict[wordcolumn] = sc_data
        if rowdict[wordcolumn] != rowdict[charcolumn]:
            rowdict["word_normalized"] = "Y"
        else:
            rowdict["word_normalized"] = "N"
        if style == "age":
            phrasecolumn = f"phrase_normalized_{target_column}"
            rowdict[phrasecolumn] = age_phrase_normalizer(sc_data)
            if rowdict[phrasecolumn] != rowdict[wordcolumn]:
                rowdict["phrase_normalized"] = "Y"
            else:
                rowdict["phrase_normalized"] = "N"
    output_spellcheck_data(sc_data_dict, WCdict, word_curation_TSV)
#    output_normalization_data(maindict)
    dict2TSV(maindict, outputTSV)


if __name__ == "__main__":
    inputTSV = sys.argv[1]
    outputTSV = sys.argv[2]
    spellcheckTSV = sys.argv[3]
    word_curation_TSV = sys.argv[4]
    target_column = sys.argv[5]
    style = sys.argv[6]
    normalize(inputTSV, outputTSV, spellcheckTSV, word_curation_TSV, target_column, style)