import re
import unicodedata as ud

message = {True: "pass", False: "fail"}

def char_valid(string):
    passing = True
    ascii_string = ud.normalize("NFKD", string).encode("ascii", "replace").decode("ascii")
    if ascii_string != string:
        passing = False
    return message[passing]

def word_valid(string, style):
    passing = True
    if style == "age":
        units = [
            "year",
            "month",
            "week",
            "day",
            "hour",
        ]
        unit_count = 0
        for unit in units:
            if unit in string:
                unit_count += 1
        if unit_count > 1:
            passing = False
    return message[passing]

def phrase_valid(input, style):
    passing = True
    if style == "age":
        passing = False
        patterns = [
            r"null",
            r"\d+\.?\d*-\d+\.?\d*\s(year|month|week|day|hour)",
            r"\d+\.?\d*\s(year|month|week|day|hour)",
            r"\d+\.?\d*\s(and|or)\s\d+\.?\d*\s(year|month|week|day|hour)",
            r"\d+\.?\d*(,?\s(and\s|or\s)?\d+\.?\d*)+\s(year|month|week|day|hour)",
            r"[a-zA-z\s]+",
            r"[<>]\d+\.?\d*\s(year|month|week|day|hour)"
                    ]
        for pattern in patterns:
            m = re.fullmatch(pattern, input)
            if m:
                passing = True
                break
    if style == "data_loc":
        for i in input:
            m = re.fullmatch(r"\d+", i)
            if m:
                passing = False
                break
    return message[passing]


def pull_invalid(data_dict, original_column):
    char_valid_col = f"char_valid?_{original_column}"
    word_valid_col = f"word_valid?_{original_column}"
    phrase_valid_col = f"phrase_valid?_{original_column}"
    invalid_dict = {}
    for index, rowdict in data_dict.items():
        if rowdict[char_valid_col] == "fail" or rowdict[word_valid_col] == "fail" or rowdict[phrase_valid_col] == "fail":
            invalid_dict[index] = rowdict.copy()
            invalid_dict[index]["curator_review"] = ""
    return invalid_dict
