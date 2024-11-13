import os
import re
import sys
import data_loc_splitter as dls
import toolkit as tk
from converter import TSV2dict, dict2TSV

separator = r"[-,\():;\s]+"


def find_category(word, word_review_dict, word_reference_dict):
    """
    Identify the category of a word based on word_reference category column.
    """
    number_regex = r"\d+\.?\d*"
    number = re.fullmatch(number_regex, word)
    if number:
        return "number"
    else:
        source, location = tk.lookup(word,
                                     word_review_dict,
                                     word_reference_dict,
                                     "word")
        if source == "reference":
            if word_reference_dict[location]["category"] != "":
                return word_reference_dict[location]["category"]
            else:
                return "unknown"
        else:
            return "unknown"


def build_phrase_dict(string, separator):
    """
    Construct a dict of information about each word in a phrase.
    """
    phrase_dict = {}
    url_regex = r"((http[s]?):\/)?\/?([^:\/\s]+)((\/\w+)*\/)(\S+)"
    url = re.fullmatch(url_regex, string)
    if url:
        phrase_dict[0] = {
            "index": 0,
            "word": string,
            "category": "url",
            "separator": "none",
        }
    else:
        string_parts = re.split(separator, string)
        separators = re.findall(separator, string)
        i = 0
        while i < len(string_parts):
            phrase_dict[i] = {}
            phrase_dict[i]["index"] = 0
            phrase_dict[i]["word"] = string_parts[i]
            phrase_dict[i]["category"] = find_category(string_parts[i],
                                                       word_review_dict,
                                                       word_reference_dict)
            if i in range(len(separators)):
                phrase_dict[i]["separator"] = separators[i]
            else:
                phrase_dict[i]["separator"] = "none"
            i += 1
    return phrase_dict


def make_categorization_string(phrase_dict):
    """
    Construct a string of the categories and locations of words in a phrase.
    """
    cat_string = ""
    for index, word_dict in phrase_dict.items():
        category = word_dict["category"]
        cat_string += f"[{category}({index})]"
    return cat_string


def phrase_lookup(cat_string):
    """
    Check cat_string against patterns specified in type sheet.
    """
    matched = False
    for index, rowdict in type_dict.items():
        pattern = rowdict["pattern"]
        if cat_string == pattern:
            return rowdict["name"], rowdict["valid?"], rowdict["standard_form"]
            matched = True
            break
    if not matched:
        return "unknown", "N", ""


def rearrange_phrase(cat_string, rowdict, phrase_dict, output_column, style):
    """
    Configure the words in cat_string according to the specified standard form.
    """
    p_type, validity, standard_form = phrase_lookup(cat_string)
    rowdict["phrase_type"] = p_type
    rowdict["phrase_validation"] = "pass" if validity == "Y" else "fail"
    phrase = standard_form
    match_list = re.findall(r"\d+", standard_form)
    for match in match_list:
        referent = phrase_dict[int(match)]["word"]
        phrase = re.sub(fr"\[{match}\]", referent, phrase)
    if style == "age":
        phrase = tk.pluralize_unit(phrase, p_type)
    rowdict[output_column] = phrase


def create_phrase_type_sheet(path):
    """
    Initialize an phrase type sheet TSV.
    """
    type_dict = {}
    type_dict[0] = {
        "index": 0,
        "name": "",
        "pattern": "",
        "valid?": "",
        "standard_form": ""
    }
    dict2TSV(type_dict, path)


def normalize_phrase(style, data_file, original_column):
    """
    Apply phrase normalization to the word-normalized data column in data_file.
    """
    target_column = f"word_normalized_{original_column}"
    output_column = f"phrase_normalized_{original_column}"
    data_dict = TSV2dict(data_file)
    if style == "data_loc":
        for index, rowdict in data_dict.items():
            data_item = rowdict[target_column]
            invalid = re.match(r"!\s.*\s!", data_item)
            if invalid:
                rowdict[f"split_{target_column}"] = data_item
            else:
                rowdict[f"split_{target_column}"] = dls.split_data_loc(rowdict[target_column])
        data_dict = dls.reindex_by_split(data_dict, f"split_{target_column}")
        target_column = f"split_phrase"
    for index, rowdict in data_dict.items():
        data_item = rowdict[target_column]
        if rowdict["word_validation"] == "fail" or rowdict["word_validation"] == "stopped":
            rowdict["phrase_type_string"] = "stopped"
            rowdict["phrase_type"] = "stopped"
            rowdict["phrase_validation"] = "stopped"
            rowdict[output_column] = data_item
        else:
            phrase_dict = build_phrase_dict(data_item, separator)
            cat_string = make_categorization_string(phrase_dict)
            rowdict["phrase_type_string"] = cat_string
            rearrange_phrase(cat_string, rowdict, phrase_dict, output_column, style)
            if rowdict["phrase_validation"] == "fail":
                phrase_type = rowdict["phrase_type"]
                rowdict[output_column] = f"! Invalid phrase type: {phrase_type} !"
    if style == "data_loc":
        dls.validity_score(data_dict)
    output_path = os.path.join(style, "output_files", f"p_norm_{style}.tsv")
    dict2TSV(data_dict, output_path)


if __name__ == "__main__":
    style = sys.argv[1]
    original_column = sys.argv[2]
    input_file = os.path.join(style, "output_files", f"w_norm_{style}.tsv")
    word_review_file = os.path.join(style, "output_files", "word_review.tsv")
    word_reference_file = os.path.join(style, "output_files", "word_reference.tsv")
    type_file = os.path.join(style, "input_files", f"{style}_phrase_types.tsv")
    if not os.path.isfile(type_file):
        create_phrase_type_sheet(type_file)
    word_review_dict = TSV2dict(word_review_file)
    word_reference_dict = TSV2dict(word_reference_file)
    type_dict = TSV2dict(type_file)
    normalize_phrase(style, input_file, original_column)
