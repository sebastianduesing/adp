from converter import TSV2dict
import csv
import sys
import unicodedata as ud
import os


def find_changed_chars(string1, string2):
    """
    Identifies characters in a string that were replaced with other characters
    during ascii normalization. Returns two strings.
    """
    charlist1 = []
    charlist2 = []
    for i in string1:
        if i not in string2:
            charlist1.append(i)
    for char in charlist1:
        if style == "age":
            ascii_char = ud.normalize("NFKD", char).encode("ascii", "replace").decode("ascii")
        else:
            ascii_char = ud.normalize("NFKD", char).encode("ascii", "ignore").decode("ascii")
        charlist2.append(ascii_char)
    charlist1 = ", ".join(charlist1)
    charlist2 = ", ".join(charlist2)
    return charlist1, charlist2


def collect_data(tracker_dict):
    """
    Creates a dict of Y/N counts from the character normalization data tracker sheet.

    -- tracker_dict: The character normalization data tracker.
    -- return: A dict of Y/N counts by field.
    """
    datadict = {}
    ascii_dict = {}
    ignored_fieldnames = ["before_char_normalization", "after_char_normalization", "index"]
    for index, rowdict in tracker_dict.items():
        if rowdict["convert_to_ascii"] == "Y":
            ascii_dict[index] = {}
            ascii_dict[index]["index"] = rowdict["index"]
            ascii_dict[index]["before_char_normalization"] = rowdict["before_char_normalization"]
            ascii_dict[index]["after_char_normalization"] = rowdict["after_char_normalization"]
            non_ascii, ascii = find_changed_chars(rowdict["before_char_normalization"], rowdict["after_char_normalization"])
            ascii_dict[index]["non_ascii_characters"] = non_ascii
            ascii_dict[index]["ascii_character_replacements"] = ascii
        for fieldname, fieldvalue in rowdict.items():
            if fieldname not in ignored_fieldnames:
                if fieldname not in datadict.keys():
                    datadict[fieldname] = {"Y": 0, "N": 0}
                if fieldvalue == "Y":
                    Y_count = datadict[fieldname]["Y"]
                    Y_count += 1
                    datadict[fieldname]["Y"] = Y_count
                else:
                    N_count = datadict[fieldname]["N"]
                    N_count += 1
                    datadict[fieldname]["N"] = N_count
    return datadict, ascii_dict


if __name__ == "__main__":
    style = sys.argv[1]
    char_norm_data_dict = TSV2dict(os.path.join(style, sys.argv[2]))  # path to character normalization data TSV
    data_path = os.path.join(style, sys.argv[3])  # path to where collected data will be stored
    ascii_path = os.path.join(style, sys.argv[4])  # path to where ascii tracker data will be stored
    data, ascii_data = collect_data(char_norm_data_dict)
    with open(data_path, "w", newline = "") as tsv:
        fieldnames = ["normalization_stage", "strings_altered", "strings_unaltered"]
        writer = csv.DictWriter(tsv, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for category, counts in data.items():
            writer.writerow({
                                "normalization_stage": category,
                                "strings_altered": counts["Y"],
                                "strings_unaltered": counts["N"]
                            })
    with open(ascii_path, "w", newline = "") as tsv:
        fieldnames = [
            "index",
            "before_char_normalization",
            "after_char_normalization",
            "non_ascii_characters",
            "ascii_character_replacements"
        ]
        writer = csv.DictWriter(tsv, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for index, row in ascii_data.items():
            writer.writerow(row)
    print(f"{ascii_path} written and saved.")
    print(f"{data_path} written and saved.")
