import sys
from converter import TSV2dict, dict2TSV


def merge_curated(curated_tsv, sorted_tsv, output_path):
    """
    Merges manually-curated rows with script-sorted rows.

    -- curated_tsv: The path of the manually-curated TSV.
    -- sorted_tsv: The path of the script-sorted TSV.
    -- output_path: The path to which the merged TSV will be written.
    """
    curated = TSV2dict(curated_tsv)
    sorted = TSV2dict(sorted_tsv)
    fieldnames = [
        "exact_age",
        "mean_age",
        "median_age",
        "minimum_age",
        "maximum_age",
        "age_list",
        "unit",
        "age_description"
        ]
    for index, rowdict in curated.items():
        checkempty = True
        for fieldname in fieldnames:
            if sorted[index][fieldname] != "":
                checkempty = False
        if checkempty:
            for fieldname in fieldnames:
                sorted[index][fieldname] = curated[index][fieldname]
                sorted[index]["age_data_type"] = "manual"
    dict2TSV(sorted, output_path)


if __name__ == "__main__":
    curatedTSV = sys.argv[1]
    sortedTSV = sys.argv[2]
    outputTSV = sys.argv[3]
    merge_curated(curatedTSV, sortedTSV, outputTSV)
