from converter import TSV2dict
import csv
import sys

def collect_data(tracker_dict):
    """
    Creates a dict of Y/N counts from the character normalization data tracker sheet.

    -- tracker_dict: The character normalization data tracker.
    -- return: A dict of Y/N counts by field.
    """
    datadict = {}
    ignored_fieldnames = ["before_char_normalization", "after_char_normalization", "index"]
    for index, rowdict in tracker_dict.items():
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
    return datadict


if __name__ == "__main__":
    char_norm_data_dict = TSV2dict(sys.argv[1])
    data_path = sys.argv[2]
    data = collect_data(char_norm_data_dict)
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
    print(f"{data_path} written and saved.")
