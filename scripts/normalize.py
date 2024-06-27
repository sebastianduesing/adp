import csv
import sys
import os
import re
import editdistance
import pandas as pd
from converter import TSV2dict, dict2TSV
import data_loc_splitter as splt
import text_formatter as tf
import validator as vl

# TODO: Check if this is still needed and remove if not
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


def stripped_data_loc(data_loc_dict):
    """
    Outputs a version of the normalized data_loc file with only one line per
    index (i.e., removing all but the first parts of split lines) so that
    split lines don't skew data normalization metrics.  

    -- data_loc_dict: The normalized dict of data-loc data.
    -- return: Stripped version of data_loc_dict with 1 line per original line.
    """
    index_list = []
    stripped = data_loc_dict.copy()
    for index, rowdict in data_loc_dict.items():
        if rowdict["index"] in index_list:
            del stripped[index]
        else:
            index_list.append(rowdict["index"])
    return stripped

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


def output_spellcheck_data(sc_data_dict, WCdict, word_curation_TSV, target_column, style):
    """
    Logs frequency data for spellcheck replacements in <style>_spellcheck_data.tsv.
    Also logs unknown words stored in WCdict in word_curation_TSV.

    -- sc_data_dict: A dict of spellcheck data.
    -- WCdict: A dict of words to be manually curated.
    -- word_curation_TSV: Path to the TSV that stores word curation data.
    """
    with open(os.path.join(style, f"output_files/{style}_spellcheck_data.tsv"), "w", newline="\n") as tsvfile:
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


def normalize(inputTSV, outputTSV, char_norm_data_TSV, spellcheckTSV, word_curation_TSV, target_column, style):
    """
    Applies normalization steps to all data items in target column or columns
    in an input TSV, creates a new column for the normalized data, and writes
    updated TSV to an output path.

    -- inputTSV: Path of TSV to be normalized.
    -- outputTSV: Path of TSV with new normalized data.
    -- char_norm_data_TSV: Path of TSV to store character normalization data.
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
    char_norm_data_dict = {}
    
    char_column = f"char_normalized_{target_column}"
    word_column = f"word_normalized_{target_column}"
    phrase_column = f"phrase_normalized_{target_column}"

    char_valid_column = f"char_valid?_{target_column}"
    word_valid_column = f"word_valid?_{target_column}"
    phrase_valid_column = f"phrase_valid?_{target_column}"
    
    char_score_column = f"char_normalization_score_{target_column}"
    word_score_column = f"word_normalization_score_{target_column}"
    phrase_score_column = f"phrase_normalization_score_{target_column}"
    overall_score_column = f"overall_normalization_score_{target_column}"
    
    for index, rowdict in maindict.items():
        original_data = rowdict[target_column]
        data, char_norm_data = tf.char_normalizer(original_data)
        char_norm_data["index"] = index
        char_norm_data_dict[index] = char_norm_data

        rowdict[char_column] = data
        rowdict["char_normalized"] = "Y" if rowdict[char_column] != original_data else "N"
        rowdict[char_valid_column] = vl.char_valid(data)
        rowdict[char_score_column] = editdistance.eval(original_data, data)
        
        sc_data = tf.word_normalizer(data, SCdict, WCdict, sc_data_dict)
        rowdict[word_column] = sc_data
        rowdict["word_normalized"] = "Y" if rowdict[word_column] != rowdict[char_column] else "N"
        rowdict[word_valid_column] = vl.word_valid(sc_data, style)
        rowdict[word_score_column] = editdistance.eval(rowdict[char_column], rowdict[word_column])
        
        if style == "age":
            rowdict[phrase_column] = tf.phrase_normalizer(sc_data, style)
            # Simple check to see if the phrase was normalized
            rowdict["phrase_normalized"] = "Y" if rowdict[phrase_column] != rowdict[word_column] else "N"
            rowdict[phrase_valid_column] = vl.phrase_valid(rowdict[phrase_column], style)
            rowdict[phrase_score_column] = editdistance.eval(sc_data, rowdict[phrase_column])
            rowdict[overall_score_column] = editdistance.eval(original_data, rowdict[phrase_column])
        elif style == "data_loc":
            rowdict[phrase_column] = tf.phrase_normalizer(sc_data, style)
            # Because this is a list, extract first element to check if it was normalized
            if rowdict[phrase_column] and rowdict[word_column]:
                rowdict["phrase_normalized"] = "Y" if rowdict[phrase_column][0] != rowdict[word_column] else "N"
            # TODO: Hits this 31 times... why????
            # Some issue with specific phrases containing "and"
            else:
                print(f" -------- CURR INDEX: {index} -------- ")
                print(f"FOUND AT {word_column} in rowdict: {rowdict[word_column]}")
                print(f"FOUND AT {phrase_column} in rowdict: {rowdict[phrase_column]}")
                rowdict["phrase_normalized"] = "WTF"       
            rowdict[phrase_valid_column] = vl.phrase_valid(rowdict[phrase_column], style)
            rowdict[phrase_score_column] = editdistance.eval(sc_data, rowdict[phrase_column])
            rowdict[overall_score_column] = editdistance.eval(original_data, rowdict[phrase_column])
        else:
            print(f"Error: {style} is not a valid style.")
            sys.exit(1)
    
    # Output spellcheck data and unknown words for manual curation.        
    output_spellcheck_data(sc_data_dict, WCdict, word_curation_TSV, target_column, style)
    
    # Add additional columns to the TSV to finalize data location normalization.
    # TODO: Decide on this or go with inserted N/A values.
    if style == "data_loc":
        # Convert dict to DataFrame, normalize, and convert back
        df = splt.dict_to_dataframe(maindict, phrase_column)
        final_dict = splt.dataframe_to_dict(df)
        stripped = stripped_data_loc(final_dict)
        dict2TSV(stripped, os.path.join("data_loc", "output_files", "stripped_data_loc.tsv"))
    if style == "age":
        final_dict = maindict
    dict2TSV(final_dict, outputTSV)
    dict2TSV(char_norm_data_dict, char_norm_data_TSV)


if __name__ == "__main__":
    # Check style; also name of directory where TSVs are found/stored.
    style = sys.argv[7]
    # Create the paths for the input and output TSVs.
    inputTSV = os.path.join(style, sys.argv[1])
    outputTSV = os.path.join(style, sys.argv[2])
    char_norm_data_TSV = os.path.join(style, sys.argv[3])
    spellcheckTSV = os.path.join(style, sys.argv[4])
    word_curation_TSV = os.path.join(style, sys.argv[5])
    target_column = sys.argv[6]
    # Verify that the files exist.
    file_paths = [inputTSV, spellcheckTSV, word_curation_TSV]
    for path in file_paths:
        if not os.path.isfile(path):
            print(f"Error: {path} does not exist.")
            sys.exit(1)
    normalize(inputTSV, outputTSV, char_norm_data_TSV, spellcheckTSV, word_curation_TSV, target_column, style)
