import os
import re
import sys
from converter import TSV2dict, dict2TSV


def build_regex_library(phrase_kit):
    phrase_kit = TSV2dict(phrase_kit)
    builder_dict = {}
    format_dict = {}
    part_dict = {}
    for index, rowdict in phrase_kit.items():
        name = rowdict["name"]
        builder_dict[name] = {}
        builder_dict[name]["type"] = rowdict["type"]
        regex_text = rowdict["regex"]
        regex = fr"{regex_text}"
        m = re.match(r"{{[a-z_]+}}", regex)
        if m:
            matchset = set(re.findall(r"{{[a-z_]+}}", regex))
            for match in matchset:
                text = re.findall(r"[^{}]+", match)
                text = text[0]
                referenced_part = builder_dict[text]["regex"]
                referenced_part = fr"({referenced_part})"
                regex = re.sub(match, referenced_part, regex)
        if r"&&" in regex:
            regex = regex.split(r"&&")
            standard_form = rowdict["standard_form"].split(r"&&")
            rowdict["standard_form"] = standard_form
        builder_dict[name]["regex"] = regex
        builder_dict[name]["valid?"] = rowdict["valid?"]
        standard_form = rowdict["standard_form"]
        builder_dict[name]["standard_form"] = standard_form
    for regex_name, infodict in builder_dict.items():
        if infodict["type"] == "format":
            format_dict[regex_name] = infodict.copy()
        if infodict["type"] == "part":
            part_dict[regex_name] = infodict.copy()
    return format_dict, part_dict


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
    formats, parts = build_regex_library(phrase_kit)
    for index, rowdict in data_dict.items():
        data_item = rowdict[target_column]
        rowdict["format"] = ""
        rowdict["phrase_validation"] = "fail"
        rowdict[f"phrase_normalized_{target_column}"] = ""
        stopped = re.fullmatch(r"! .* !", data_item)
        if stopped:
            rowdict["format"] = "stopped"
            rowdict["phrase_validation"] = "stopped"
            continue
        matched = False
        for format, format_info in formats.items():
            regex = format_info["regex"]
            standard = format_info["standard_form"]
            if type(regex) is list:
                for i in range(len(regex)):
                    r = regex[i]
                    m = re.fullmatch(r, data_item)
                    if m:
                        matched = True
                        regex = r
                        standard = format_info["standard_form"][i]
                        break
            else:
                m = re.fullmatch(regex, data_item)
            if m:
                rowdict["format"] = format
                rowdict["phrase_validation"] = validate_format(format_info, "string")
                if validate_format(format_info, "boolean"):
                    rowdict[f"phrase_normalized_{target_column}"] = re.sub(regex, standard, data_item)
                matched = True
                break
        if not matched:
            rowdict["format"] = "unknown"
    output_path = os.path.join(style, "output_files", f"p_norm_{style}.tsv")
    dict2TSV(data_dict, output_path)


if __name__ == "__main__":
    style = sys.argv[1]
    input_file = os.path.join(style, "output_files", f"w_norm_{style}.tsv")
    target_column = f"word_normalized_char_normalized_{sys.argv[2]}"
    phrase_kit = os.path.join(style, "input_files", f"{style}_phrase_kit.tsv")
    normalize_phrases(style, input_file, target_column)
