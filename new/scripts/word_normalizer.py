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
    word_set = make_word_set(string)
    for word in word_set:
        m = re.fullmatch(word_regex, word)
        if not m:
            invalid_words.add(word)
    return invalid_words


def make_word_set(string):
    """
    Return a set of all words in a string.
    """
    delimiters = [",", ".", "-", " ", "(", ")", ":", ";", "+", "=", ">", "<"]
    string_stripped = string
    for delimiter in delimiters:
        string_stripped = " ".join(string_stripped.split(delimiter))
    word_list = string_stripped.split(" ")
    word_set = set(word_list)
    return word_set


def take_action(reference_dict, invalid_word, data_item, index):
    """
    Alters data_item as specified in reference_dict.

    This may be moved to toolkit later; I have suspicions that word
    substitution will require more finesse (dealing with punctuation and
    delimiters, etc.), so it will probably be preferable to just build out a
    word-specific version of this function. To be determined.
    """
    if reference_dict[index]["replace_with"] != "":
        replacement = reference_dict[index]["replace_with"]
        data_item = re.sub(invalid_word, replacement, data_item)
    elif reference_dict[index]["remove"] != "":
        data_item = re.sub(invalid_word, "", data_item)
    return data_item


def normalize_words(style, data_file, target_column, review_file, reference_file):
    """
    Performs word normalization on target_column in data_file.

    Reads or creates reference & review dicts, attempts to replace or remove
    invalid words in those data items if possible, and if no replacement has
    been specified, adds them to review file for manual review.
    """
    data_dict = TSV2dict(data_file)
    allowed_words = set()
    if os.path.isfile(review_file):
        review_dict = TSV2dict(review_file)
    else:
        review_dict = {}
    if os.path.isfile(reference_file):
        reference_dict = TSV2dict(reference_file)
    else:
        reference_dict = {}
    review_dict, reference_dict = tk.update_reference(review_dict, reference_dict)
    for index, rowdict in data_dict.items():
        data_item = rowdict[target_column]
        if style == "data_loc":
            m = re.fullmatch(r"https:\/\/hla-ligand-atlas.org\/peptide\/[a-zA-Z]+", data_item)
            if m:
                rowdict["word_validation"] = "pass"
                rowdict[f"word_normalized_{target_column}"] = data_item
                continue
        invalid_words = identify_invalid_words(data_item)
        rowdict["word_validation"] = tk.validate(invalid_words, "string")
        if tk.validate(invalid_words, "boolean"):
            rowdict[f"word_normalized_{target_column}"] = data_item
        else:
            for word in invalid_words:
                source, location = tk.lookup(word, review_dict, reference_dict, "word")
                if source == "reference":
                    data_item = take_action(reference_dict,
                                            word,
                                            data_item,
                                            location)
                    data_stripped = data_item.strip()
                    data_item = re.sub(r"(\s\s+)", r" ", data_stripped)
                    if reference_dict[location]["allow"] != "":
                        allowed_words.add(word)
                elif source == "review":
                    if data_item not in review_dict[location]["context"]:
                        if len(review_dict[location]["context"]) < 300:
                            context_string = review_dict[location]["context"]
                            context_string += f""", '{data_item}'"""
                            occurrences = int(review_dict[location]["occurrences"])
                            occurrences += 1
                            review_dict[location]["occurrences"] = occurrences
                            review_dict[location]["context"] = context_string
                else:
                    id = tk.next_index(review_dict)
                    review_dict[id] = {}
                    review_dict[id]["index"] = id
                    review_dict[id]["invalid_word"] = word
                    review_dict[id]["context"] = f"""'{data_item}'"""
                    review_dict[id]["occurrences"] = 1
                    review_dict[id]["replace_with"] = ""
                    review_dict[id]["remove"] = ""
                    review_dict[id]["invalidate"] = ""
                    review_dict[id]["allow"] = ""
            invalid_words = identify_invalid_words(data_item)
            for word in invalid_words.copy():
                if word in allowed_words:
                    invalid_words.remove(word)
            rowdict["word_validation"] = tk.validate(invalid_words, "string")
            if tk.validate(invalid_words, "boolean"):
                rowdict[f"word_normalized_{target_column}"] = data_item
            else:
                rowdict[f"word_normalized_{target_column}"] = f"! {invalid_words} !"
    output_path = os.path.join(style, "output_files", f"w_norm_{style}.tsv")
    dict2TSV(data_dict, output_path)
    if len(review_dict.keys()) != 0:
        dict2TSV(review_dict, review_file)
    if len(reference_dict.keys()) != 0:
        dict2TSV(reference_dict, reference_file)


if __name__ == "__main__":
    style = sys.argv[1]
    input_file = os.path.join(style, sys.argv[2])
    target_column = f"char_normalized_{sys.argv[3]}"
    review = os.path.join(style, "output_files", "word_review.tsv")
    reference = os.path.join(style, "output_files", "word_reference.tsv")

    if style == "age":
        style_words = [
            "year",
            "month",
            "week",
            "day",
            "hour",
            "adult",
            "child",
            "mean",
            "median",
            "average"
        ]
    if style == "data_loc":
        style_words = [
            "table",
            "figure",
            "supplemental",
            "reference",
            "data",
            "abstract",
            "title",
            "page",
            "pdb",
            "extended",
            r"[0-9][a-z0-9]{3}",  # PDB identifier format
        ]
    general_words = [
        "and",
        "or",
        r"\d+"
    ]
    approved_words = general_words + style_words
    word_regex = build_regex_from_list(approved_words)
    normalize_words(style, input_file, target_column, review, reference)
