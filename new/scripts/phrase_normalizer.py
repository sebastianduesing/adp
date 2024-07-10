import os
import re
import sys
from converter import TSV2dict, dict2TSV


def build_regex_library(phrase_kit):
    phrase_kit = TSV2dict(phrase_kit)
    builder_dict = {}
    format_dict = {}
    for index, rowdict in phrase_kit.items():
        name = rowdict["name"]
        builder_dict[name] = {}
        builder_dict[name]["type"] = rowdict["type"]
        regex_text = rowdict["regex"]
        regex_string = fr"{regex_text}"
        regex_string = fr"{regex_string}"
        m = re.match(r"{{[a-z_]+}}", regex_string)
        if m:
            matchset = set(re.findall(r"{{[a-z_]+}}", regex_string))
            for match in matchset:
                text = re.findall(r"[^{}]+", match)
                text = text[0]
                referenced_part = builder_dict[text]["regex"]
                referenced_part = fr"({referenced_part})"
                regex_string = re.sub(match, referenced_part, regex_string)
        builder_dict[name]["regex"] = regex_string
        builder_dict[name]["valid?"] = rowdict["valid?"]
    for regex_name, infodict in builder_dict.items():
        if infodict["type"] == "format":
            format_dict[regex_name] = infodict.copy()
    return format_dict


def validate_format(format_dict, mode):
    response_dict = {
        "Y": {"string": "pass", "boolean": True},
        "N": {"string": "fail", "boolean": False}
    }
    valid = format_dict["valid?"]
    return response_dict[valid][mode]


def normalize_phrases(style, data_file, target_column):
    """
    Perform phrase normalization on target_column in data_file.
    """
    data_dict = TSV2dict(data_file)
    formats = build_regex_library(phrase_kit)
    for index, rowdict in data_dict.items():
        data_item = rowdict[target_column]
        stopped = re.fullmatch(r"! .* !", data_item)
        if stopped:
            rowdict["format"] = "stopped"
            rowdict["phrase_validation"] = "stopped"
            continue
        matched = False
        for format, format_info in formats.items():
            regex = format_info["regex"]
            m = re.fullmatch(regex, data_item)
            if m:
                rowdict["format"] = format
                rowdict["phrase_validation"] = validate_format(format_info, "string")
                matched = True
                break
        if not matched:
            rowdict["format"] = "unknown"
            rowdict["phrase_validation"] = "fail"
    output_path = os.path.join(style, "output_files", f"p_norm_{style}.tsv")
    dict2TSV(data_dict, output_path)


if __name__ == "__main__":
    style = sys.argv[1]
    input_file = os.path.join(style, "output_files", f"w_norm_{style}.tsv")
    target_column = f"word_normalized_char_normalized_{sys.argv[2]}"
    phrase_kit = os.path.join(style, "input_files", f"{style}_phrase_kit.tsv")
    normalize_phrases(style, input_file, target_column)
