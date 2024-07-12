import os
import re
import sys
import toolkit as tk
from converter import TSV2dict, dict2TSV

separator = r"[-,\.():;\s]+"


def find_category(word, word_review_dict, word_reference_dict):
    number_regex = r"\d+\.?\d*"
    number = re.match(number_regex, word)
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
        cat_string += f"[{category}]"
    return cat_string


def normalize_phrase(style, data_file, original_column):
    target_column = f"word_normalized_{original_column}"
    data_dict = TSV2dict(data_file)
    for index, rowdict in data_dict.items():
        data_item = rowdict[target_column]
        stopped = re.fullmatch(r"! .* !", data_item)
        if stopped:
            rowdict[f"phrase_type_string"] = "[invalid]"
            continue
        phrase_dict = build_phrase_dict(data_item, separator)
        cat_string = make_categorization_string(phrase_dict)
        rowdict[f"phrase_type_string"] = cat_string
    output_path = os.path.join(style, "output_files", f"p_norm_{style}.tsv")
    dict2TSV(data_dict, output_path)


if __name__ == "__main__":
    style = sys.argv[1]
    original_column = sys.argv[2]
    input_file = os.path.join(style, "output_files", f"w_norm_{style}.tsv")
    word_review_file = os.path.join(style, "output_files", "word_review.tsv")
    word_reference_file = os.path.join(style, "output_files", "word_reference.tsv")
    word_review_dict = TSV2dict(word_review_file)
    word_reference_dict = TSV2dict(word_reference_file)
    normalize_phrase(style, input_file, original_column)
