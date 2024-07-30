import sys
import csv
import os
import numpy as np
from converter import TSV2dict

def gather_score_data(normalized_data, original_column, output_path):
    c_norm_score_col = f"char_normalization_score_{original_column}"
    w_norm_score_col = f"word_normalization_score_{original_column}"
    p_norm_score_col = f"phrase_normalization_score_{original_column}"
    overall_score_col = f"overall_normalization_score_{original_column}"
    c_score_list = []
    w_score_list = []
    p_score_list = []
    o_score_list = []
    for index, rowdict in normalized_data.items():
        pairs = [
            (c_score_list, rowdict[c_norm_score_col]),
            (w_score_list, rowdict[w_norm_score_col]),
            (p_score_list, rowdict[p_norm_score_col]),
            (o_score_list, rowdict[overall_score_col])
        ]
        for (scorelist, value) in pairs:
            try:
                scorelist.append(int(value))
            except TypeError:
                pass
    score_data = {}
    for scores in [c_score_list, w_score_list, p_score_list, o_score_list]:
        if scores == c_score_list:
            score_data["character_normalization_score"] = {}
            working_dict = score_data["character_normalization_score"]
            working_dict["phase"] = "character"
        if scores == w_score_list:
            score_data["word_normalization_score"] = {}
            working_dict = score_data["word_normalization_score"]
            working_dict["phase"] = "word"
        if scores == p_score_list:
            score_data["phrase_normalization_score"] = {}
            working_dict = score_data["phrase_normalization_score"]
            working_dict["phase"] = "phrase"
        if scores == o_score_list:
            score_data["overall_normalization_score"] = {}
            working_dict = score_data["overall_normalization_score"]
            working_dict["phase"] = "overall"
        working_dict["minimum"] = min(scores)
        working_dict["maximum"] = max(scores)
        working_dict["median"] = np.median(scores)
        working_dict["mean"] = round(np.mean(scores), 2)
        working_dict["standard_deviation"] = round(np.std(scores), 2)
        working_dict["variance"] = round(np.var(scores), 2)
    with open(output_path, "w", newline="") as tsvfile:
        fieldnames = [
            "phase",
            "minimum",
            "maximum",
            "median",
            "mean",
            "standard_deviation",
            "variance"
        ]
        writer = csv.DictWriter(tsvfile, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for phase, phase_data in score_data.items():
            writer.writerow(phase_data)
        print(f"Data written to {output_path}.")

if __name__ == "__main__":
    style = sys.argv[1]
    normalized_data = TSV2dict(os.path.join(style, sys.argv[2]))
    original_column = sys.argv[3]
    output_path = os.path.join(style, sys.argv[4])
    gather_score_data(normalized_data, original_column, output_path)
