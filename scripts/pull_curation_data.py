import os
import sys
from converter import dict2TSV, TSV2dict


def get_data_from_file(filename, data_dict, target_column):
    file_data = TSV2dict(filename)
    for index, rowdict in file_data.items():
        if rowdict[target_column] in data_dict.keys():
            count = data_dict[rowdict[target_column]]["occurrences"]
            count += 1
            data_dict[rowdict[target_column]]["occurrences"] = count
        else:
            data_dict[rowdict[target_column]] = {}
            data_dict[rowdict[target_column]][target_column] = rowdict[target_column]
            data_dict[rowdict[target_column]]["occurrences"] = 1
    return data_dict


def main():
    style = sys.argv[1]
    target_column = sys.argv[2]
    groups = ["bcell", "tcell", "mhc_elution"]
    accepted_files = [f"{group}_accepted_{style}.tsv" for group in groups]
    normalized_files = [f"{group}_updated_{style}.tsv" for group in groups]
    invalid_files = [f"{group}_invalid_{style}.tsv" for group in groups]
    remaining_files = [f"{group}_remaining_{style}.tsv" for group in groups]
    for i in [accepted_files, normalized_files, invalid_files, remaining_files]:
        data_dict = {}
        for file in i:
            path = os.path.join(style, "output_files", "iedb_data", file)
            data_dict = get_data_from_file(path, data_dict, target_column)
        if i == accepted_files:
            output_path = os.path.join(style, "output_files", "iedb_data", f"accepted_curation_{style}.tsv")
        elif i == normalized_files:
            output_path = os.path.join(style, "output_files", "iedb_data", f"updated_curation_{style}.tsv")
        elif i == invalid_files:
            output_path = os.path.join(style, "output_files", "iedb_data", f"invalid_curation_{style}.tsv")
        elif i == remaining_files:
            output_path = os.path.join(style, "output_files", "iedb_data", f"remaining_curation_{style}.tsv")
        dict2TSV(data_dict, output_path)


if __name__ == "__main__":
    main()
