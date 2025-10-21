import os
import re
import sys
from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Sequence, Tuple

import toolkit as tk
from converter import TSV2dict, dict2TSV
from normalization_utils import (
    dataframe_to_indexed_dict,
    dict_to_dataframe,
    ensure_dict,
)

DEFAULT_APPROVED_WORDS = ["are", "is", "than", r"\d+"]
DEFAULT_DELIMITERS = [",", ".", "-", " ", "(", ")", ":", ";"]


@dataclass
class WordNormalizationResult:
    data: Dict[int, Dict[str, str]]
    review: Dict[int, Dict[str, str]]
    reference: Dict[int, Dict[str, str]]


def build_regex_from_list(list_of_strings: Sequence[str]) -> str:
    """
    Create a regex that matches any string from a list of strings.
    """
    if not list_of_strings:
        return r".*"
    regex = fr"{list_of_strings[0]}"
    for i in range(1, len(list_of_strings)):
        regex += fr"|{list_of_strings[i]}"
    return regex


def identify_invalid_words(string: str, word_regex: str, delimiters: Iterable[str]) -> set:
    """
    Return a set of invalid words found a string.
    """
    invalid_words = set()
    word_set = make_word_set(string, delimiters)
    for word in word_set:
        if not re.fullmatch(word_regex, word):
            invalid_words.add(word)
    return invalid_words


def make_word_set(string: str, delimiters: Iterable[str]) -> set:
    """
    Return a set of all words in a string.
    """
    string_stripped = string
    for delimiter in delimiters:
        string_stripped = " ".join(string_stripped.split(delimiter))
    word_list = string_stripped.split(" ")
    word_set = set(word_list)
    word_set.discard("")
    return word_set


def normalize_words_dict(style: str,
                         data_dict: Dict[int, Dict[str, str]],
                         original_column: str,
                         review_dict: Optional[Dict[int, Dict[str, str]]] = None,
                         reference_dict: Optional[Dict[int, Dict[str, str]]] = None,
                         approved_words: Optional[Sequence[str]] = None,
                         delimiters: Optional[Sequence[str]] = None) -> WordNormalizationResult:
    """
    Performs word normalization on target_column in data_file.

    Reads or creates reference & review dicts, attempts to replace or remove
    invalid words in those data items if possible, and if no replacement has
    been specified, adds them to review file for manual review.
    """
    target_column = f"char_normalized_{original_column}"
    new_column = f"word_normalized_{original_column}"
    approved_words = approved_words or DEFAULT_APPROVED_WORDS
    delimiters = delimiters or DEFAULT_DELIMITERS
    word_regex = build_regex_from_list(approved_words)
    allowed_words = set()
    review_dict = ensure_dict(review_dict)
    reference_dict = ensure_dict(reference_dict)
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
                rowdict = tk.evaluate_ld(rowdict,
                                         "word",
                                         target_column,
                                         new_column)
                continue
        invalid_words = identify_invalid_words(data_item, word_regex, delimiters)
        rowdict["word_validation"] = tk.validate(invalid_words, "string")
        if tk.validate(invalid_words, "boolean"):
            rowdict[new_column] = data_item.strip()
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
            invalid_words = identify_invalid_words(data_item, word_regex, delimiters)
            for word in invalid_words.copy():
                if word in allowed_words:
                    invalid_words.remove(word)
            rowdict["word_validation"] = tk.validate(invalid_words, "string")
            if tk.validate(invalid_words, "boolean"):
                rowdict[new_column] = data_item.strip()
            else:
                rowdict[new_column] = f"! Invalid words: {sorted(invalid_words)} !"
        rowdict = tk.evaluate_ld(rowdict,
                                 "word",
                                 target_column,
                                 new_column)

    return WordNormalizationResult(data_dict, review_dict, reference_dict)


def normalize_words_dataframe(style: str,
                              dataframe,
                              original_column: str,
                              review_df=None,
                              reference_df=None,
                              approved_words: Optional[Sequence[str]] = None,
                              delimiters: Optional[Sequence[str]] = None) -> Tuple:
    data_dict = dataframe_to_indexed_dict(dataframe)
    review_dict = dataframe_to_indexed_dict(review_df)
    reference_dict = dataframe_to_indexed_dict(reference_df)
    result = normalize_words_dict(style,
                                  data_dict,
                                  original_column,
                                  review_dict,
                                  reference_dict,
                                  approved_words,
                                  delimiters)
    return (
        dict_to_dataframe(result.data),
        dict_to_dataframe(result.review),
        dict_to_dataframe(result.reference),
    )


def normalize_words(style, data_file, original_column, review_file, reference_file,
                    approved_words: Optional[Sequence[str]] = None,
                    delimiters: Optional[Sequence[str]] = None):
    data_dict = TSV2dict(data_file)
    review_dict = TSV2dict(review_file) if os.path.isfile(review_file) else {}
    reference_dict = TSV2dict(reference_file) if os.path.isfile(reference_file) else {}
    result = normalize_words_dict(style,
                                  data_dict,
                                  original_column,
                                  review_dict,
                                  reference_dict,
                                  approved_words,
                                  delimiters)
    output_path = os.path.join(style, "output_files", f"w_norm_{style}.tsv")
    dict2TSV(result.data, output_path)
    if len(result.review.keys()) != 0:
        dict2TSV(result.review, review_file)
    if len(result.reference.keys()) != 0:
        dict2TSV(result.reference, reference_file)


if __name__ == "__main__":
    style = sys.argv[1]
    input_file = os.path.join(style, "output_files", f"c_norm_{style}.tsv")
    original_column = sys.argv[2]
    review = os.path.join(style, "output_files", "word_review.tsv")
    reference = os.path.join(style, "output_files", "word_reference.tsv")
    normalize_words(style, input_file, original_column, review, reference,
                    approved_words=DEFAULT_APPROVED_WORDS,
                    delimiters=DEFAULT_DELIMITERS)
