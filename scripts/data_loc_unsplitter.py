import os
import sys
import re
from converter import TSV2dict, dict2TSV


def make_part_index(data_dict):
    """
    Get a dict of original indices and all indices derived from them.
    """
    index_lookup = {}
    for index, rowdict in data_dict.items():
        if rowdict["original_index"] not in index_lookup.keys():
            index_lookup[rowdict["original_index"]] = []
        index_lookup[rowdict["original_index"]].append(index)
    return index_lookup


def make_clean_output(output_dict):
    output_list = []
    for category, contents in output_dict.items():
        if len(contents) > 1:
            category_string = f"{category}s "
        else:
            category_string = f"{category} "
        content_string = ", ".join(contents)
        full_string = category_string + content_string
        output_list.append(full_string)
    output_string = "; ".join(sorted(output_list))
    return output_string


def write_clean_output_col(data_dict, clean_outputs, original_column):
    unused_cols = [
        "char_validation",
        f"char_normalized_{original_column}",
        "char_distance_score",
        "word_validation",
        f"word_normalized_{original_column}",
        "word_distance_score",
    ]
    working_id = None
    for index, rowdict in data_dict.items():
        for column in unused_cols:
            del rowdict[column]
        og_id = rowdict["original_index"]
        if og_id in clean_outputs.keys() and og_id != working_id:
            rowdict["clean_output"] = clean_outputs[og_id]
        else:
            rowdict["clean_output"] = ""
        working_id = og_id
    return data_dict


def unsplit(data_dict, original_column):
    clean_outputs = {}
    index_lookup = make_part_index(data_dict)
    for og_id, line_ids in index_lookup.items():
        output = {}
        rows = {}
        starter_row = line_ids[0]
        if data_dict[starter_row]["phrase_validity_rate"] != "1.0":
            continue
        for line_id in line_ids:
            rows[line_id] = data_dict[line_id]
        for line_id, row in rows.items():
            phrase = row[f"phrase_normalized_{original_column}"]
            if row["phrase_type"] == "url":
                output["URL"] = [phrase,]
            if row["phrase_type"] in ["format_number", "loc_number", "loc_format_number"]:
                m = re.match(r"(.+)(\s)([a-z0-9]+)", phrase)
                if m:
                    category = m.group(1)
                    number = m.group(3)
                    if category not in output.keys():
                        output[category] = [number,]
                    else:
                        value_list = output[category]
                        value_list.append(number)
                        output[category] = value_list
            if row["phrase_type"] == "pdb_id":
                category = "PDB ID"
                number = re.match(r"(.+)(\s)([a-z0-9]+)", phrase).group(3)
                if category not in output.keys():
                    output[category] = [number,]
                else:
                    value_list = output[category]
                    value_list.append(number)
                    output[category] = value_list
        output_string = make_clean_output(output)
        clean_outputs[og_id] = output_string
    data_dict = write_clean_output_col(data_dict, clean_outputs, original_column)
    return data_dict


def main():
    style = sys.argv[1]
    original_column = sys.argv[2]
    infile = os.path.join(style, "output_files", f"p_norm_{style}.tsv")
    outfile = os.path.join(style, "output_files", "p_norm_data_loc_clean.tsv")
    data_dict = TSV2dict(infile)
    data_dict = unsplit(data_dict, original_column)
    dict2TSV(data_dict, outfile)


if __name__ == "__main__":
    main()
