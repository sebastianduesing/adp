import os
import re
import sys
from converter import dict2TSV, TSV2dict


def make_source(normalized_data_path, target_column):
    datadict = TSV2dict(normalized_data_path)
    source = {}
    for index, rowdict in datadict.items():
        normalized_string = rowdict[f"phrase_normalized_{target_column}"]
        starting_string = rowdict[target_column]
        invalid = re.match(r"!\s.*\s!", normalized_string)
        if not invalid:
            source[starting_string] = normalized_string
    return source


def update_data(input, source, target_column):
    updated_data, accepted_data, remaining_data = {}, {}, {}
    input_count = len(input.keys())
    for index, rowdict in input.items():
        data_item = rowdict[target_column]
        if data_item in source.keys() and data_item != source[data_item]:
            updated_data[index] = {}
            for key, val in rowdict.items():
                if key != "index":
                    updated_data[index][key] = val
            updated_data[index][f"new_{target_column}"] = source[data_item]
        elif data_item in source.keys():
            accepted_data[index] = {}
            for key, val in rowdict.items():
                if key != "index":
                    accepted_data[index][key] = val
        else:
            remaining_data[index] = {}
            for key, val in rowdict.items():
                if key != "index":
                    remaining_data[index][key] = val
    return updated_data, accepted_data, remaining_data, input_count


def main():
    style = sys.argv[1]
    target_column = sys.argv[2]
    normalized_data = os.path.join(style, "output_files", f"p_norm_{style}.tsv")
    source = make_source(normalized_data, target_column)
    data_collection = {}
    updated_total, accepted_total, remaining_total, input_total = 0, 0, 0, 0
    for group in ["bcell", "tcell", "mhc_elution"]:
        input_path = os.path.join(style, "input_files", "iedb_data", f"{group}_curation_{style}.tsv")
        output_dir = os.path.join(style, "output_files", "iedb_data")
        input = TSV2dict(input_path)
        updated, accepted, remaining, input_count = update_data(
                                                          input,
                                                          source,
                                                          target_column)
        dict2TSV(updated, os.path.join(output_dir, f"{group}_updated_{style}.tsv"))
        dict2TSV(accepted, os.path.join(output_dir, f"{group}_accepted_{style}.tsv"))
        dict2TSV(remaining, os.path.join(output_dir, f"{group}_remaining_{style}.tsv"))
        updated_count = len(updated.keys())
        updated_total += updated_count
        accepted_count = len(accepted.keys())
        accepted_total += accepted_count
        remaining_count = len(remaining.keys())
        remaining_total += remaining_count
        input_total += input_count
        data_collection[group] = {
            "group": group,
            "input_rows": input_count,
            "rows_normalized": updated_count,
            "normalized_%": f"{round(updated_count/input_count,2)}",
            "rows_accepted": accepted_count,
            "accepted_%": f"{round(accepted_count/input_count,2)}",
            "rows_remaining": remaining_count,
            "remaining_%": f"{round(remaining_count/input_count,2)}"
        }
    data_collection["total"] = {
        "group": "total",
        "input_rows": input_total,
        "rows_normalized": updated_total,
        "normalized_%": f"{round(updated_total/input_total,2)}",
        "rows_accepted": accepted_total,
        "accepted_%": f"{round(accepted_total/input_total,2)}",
        "rows_remaining": remaining_total,
        "remaining_%": f"{round(remaining_total/input_total,2)}"
    }
    stats_path = os.path.join(style, "output_files", "iedb_data", "normalization_stats.tsv")
    dict2TSV(data_collection, stats_path)


if __name__ == "__main__":
    main()
