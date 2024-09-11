import os
import re
import sys
import toolkit as tk
from converter import TSV2dict, dict2TSV


def build_regex_from_list(list_of_strings):
    """
    Create a regex that matches any string from a list of strings.
    """
    regex = fr"{list_of_strings[0]}"
    for i in range(len(list_of_strings)):
        if i != 0:
            regex += fr"|{list_of_strings[i]}"
    return regex


def identify_invalid_words(string):
    """
    Return a set of invalid words found a string.
    """
    invalid_words = set()
    word_set = make_word_set(string, delimiters)
    for word in word_set:
        m = re.fullmatch(word_regex, word)
        if not m:
            invalid_words.add(word)
    return invalid_words


def make_word_set(string, delimiters):
    """
    Return a set of all words in a string.
    """
    string_stripped = string
    for delimiter in delimiters:
        string_stripped = " ".join(string_stripped.split(delimiter))
    word_list = string_stripped.split(" ")
    word_set = set(word_list)
    if "" in word_set:
        word_set.remove("")
    return word_set


def normalize_words(style, data_file, original_column, review_file, reference_file):
    """
    Performs word normalization on target_column in data_file.

    Reads or creates reference & review dicts, attempts to replace or remove
    invalid words in those data items if possible, and if no replacement has
    been specified, adds them to review file for manual review.
    """
    data_dict = TSV2dict(data_file)
    target_column = f"char_normalized_{original_column}"
    new_column = f"word_normalized_{original_column}"
    allowed_words = set()
    if os.path.isfile(review_file):
        review_dict = TSV2dict(review_file)
    else:
        review_dict = {}
    if os.path.isfile(reference_file):
        reference_dict = TSV2dict(reference_file)
    else:
        reference_dict = {}
    review_dict, reference_dict, allowed_words = tk.update_reference(review_dict, reference_dict, allowed_words)
    review_dict = tk.clean_occurrences(review_dict)
    for index, rowdict in data_dict.items():
        data_item = rowdict[target_column]
        m = re.match(r"!\s.+\s!", data_item)
        if m:
            rowdict["word_validation"] = "stopped"
            rowdict[new_column] = data_item
            continue
        if style == "data_loc":
            m = re.fullmatch(r"https:\/\/hla-ligand-atlas.org\/peptide\/[a-zA-Z]+", data_item)
            if m:
                rowdict["word_validation"] = "pass"
                rowdict[new_column] = data_item
                continue
        invalid_words = identify_invalid_words(data_item)
        rowdict["word_validation"] = tk.validate(invalid_words, "string")
        if tk.validate(invalid_words, "boolean"):
            rowdict[new_column] = data_item
        else:
            review_dict, reference_dict, data_item, allowed_words = tk.handle_invalid_items(
                style,
                invalid_words,
                review_dict,
                reference_dict,
                "word",
                data_item,
                allowed_words,
                delimiters
            )
            invalid_words = identify_invalid_words(data_item)
            for word in invalid_words.copy():
                if word in allowed_words:
                    invalid_words.remove(word)
            rowdict["word_validation"] = tk.validate(invalid_words, "string")
            if tk.validate(invalid_words, "boolean"):
                rowdict[new_column] = data_item
            else:
                rowdict[new_column] = f"! Invalid words: {sorted(invalid_words)} !"
        rowdict = tk.evaluate_ld(rowdict,
                                 "word",
                                 target_column,
                                 new_column)

    output_path = os.path.join(style, "output_files", f"w_norm_{style}.tsv")
    dict2TSV(data_dict, output_path)
    if len(review_dict.keys()) != 0:
        dict2TSV(review_dict, review_file)
    if len(reference_dict.keys()) != 0:
        dict2TSV(reference_dict, reference_file)


if __name__ == "__main__":
    style = sys.argv[1]
    input_file = os.path.join(style, "output_files", f"c_norm_{style}.tsv")
    original_column = sys.argv[2]
    review = os.path.join(style, "output_files", "word_review.tsv")
    reference = os.path.join(style, "output_files", "word_reference.tsv")
    approved_words = [
        "are",
        "is",
        "than",
        r"\d+"
    ]
    delimiters = [",", ".", "-", " ", "(", ")", ":", ";"]
    word_regex = build_regex_from_list(approved_words)
    normalize_words(style, input_file, original_column, review, reference)
