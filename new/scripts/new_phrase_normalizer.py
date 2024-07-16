import os
import re
import sys
import toolkit as tk
from converter import TSV2dict, dict2TSV

separator = r"[-,\():;\s]+"


def find_category(word, word_review_dict, word_reference_dict):
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
    cat_string = ""
    for index, word_dict in phrase_dict.items():
        category = word_dict["category"]
        cat_string += f"[{category}({index})]"
    return cat_string


def phrase_lookup(cat_string):
    matched = False
    for index, rowdict in type_dict.items():
        pattern = rowdict["pattern"]
        if cat_string == pattern:
            return rowdict["name"], rowdict["valid?"], rowdict["standard_form"]
            matched = True
            break
        elif "|" in pattern:
            pattern = pattern.split("|")
            standard_form = rowdict["standard_form"]
            if standard_form != "":
                standard_form = standard_form.split()
            for i in range(len(pattern)):
                if cat_string == pattern[i]:
                    if standard_form != "":
                        standard_form = standard_form[i]
                    matched = True
                    return rowdict["name"], rowdict["valid?"], standard_form
                    break
    if not matched:
        return "unknown", "N", ""


def rearrange_phrase(cat_string, rowdict, phrase_dict):
    p_type, validity, standard_form = phrase_lookup(cat_string)
    rowdict["phrase_type"] = p_type
    rowdict["phrase_validation"] = "pass" if validity == "Y" else "fail"
    phrase = standard_form
    match_list = re.findall(r"\d+", standard_form)
    for match in match_list:
        referent = phrase_dict[int(match)]["word"]
        phrase = re.sub(fr"\[{match}\]", referent, phrase)
    rowdict["phrase_normalized"] = phrase


def create_phrase_type_sheet(path):
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
    target_column = f"word_normalized_{original_column}"
    data_dict = TSV2dict(data_file)
    for index, rowdict in data_dict.items():
        data_item = rowdict[target_column]
        if rowdict["word_validation"] == "fail" or rowdict["word_validation"] == "stopped":
            rowdict["phrase_type_string"] = "stopped"
            rowdict["phrase_type"] = "stopped"
            rowdict["phrase_validation"] = "stopped"
            rowdict["phrase_normalized"] = data_item
        else:
            phrase_dict = build_phrase_dict(data_item, separator)
            cat_string = make_categorization_string(phrase_dict)
            rowdict["phrase_type_string"] = cat_string
            rearrange_phrase(cat_string, rowdict, phrase_dict)
            if rowdict["phrase_validation"] == "fail":
                phrase_type = rowdict["phrase_type"]
                rowdict["phrase_normalized"] = f"! Invalid phrase type: {phrase_type} !"
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
