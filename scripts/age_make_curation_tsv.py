import sys
from converter import TSV2dict, dict2TSV


def find_missing_rows(fulldict, curation_dict, curation_tsv,  data_type_column):
    """
    Checks that curation_dict contains all rows of fulldict in which
    data_type_column is empty, and adds any missing empty rows as needed.

    -- fulldict: A dict containing rows curated automatically and manually,
       and possibly uncurated rows.
    -- curation_dict: A dict of manually-curated rows.
    -- data_type_column: The column that triggers a row to be put into manual
       curation if it is empty.
    """
    indexlist = []
    for index, rowdict in fulldict.items():
        if rowdict[data_type_column] == "":
            if index not in curation_dict.keys():
                curation_dict[index] = rowdict
                curation_dict[index][data_type_column] = "other"
                indexlist.append(index)
    if len(indexlist) == 0:
        print("No new uncurated rows found.")
    else:
        print(f"Found {len(indexlist)} new uncurated row(s):")
        for i in indexlist:
            print(f"\tRow {i}")
    dict2TSV(curation_dict, curation_tsv)


def create_curation_TSV(input_path, output_path, data_type_column):
    """
    Creates a TSV for manual curation based on the file specified using
    input_path. For each row, if the column specified in data_type_column is
    empty, i.e., that row has not already been automatically processed, that
    row is added to the manual curation TSV named output_path.

    -- input_path: The TSV from which rows will be pulled.
    -- output_path: The TSV for manual curation.
    -- data_type_column: The column that triggers a row to be put into manual
       curation if it is empty.
    """
    curation_dict = {}
    maindict = TSV2dict(input_path)
    for index, rowdict in maindict.items():
        if rowdict[data_type_column] == "":
            curation_dict[index] = rowdict
            curation_dict[index][data_type_column] = "other"
    dict2TSV(curation_dict, output_path)


if __name__ == "__main__":
    inputTSV = sys.argv[1]
    curationTSV = sys.argv[2]
    data_type_column = sys.argv[3]
    try:
        curationdict = TSV2dict(curationTSV)
        maindict = TSV2dict(inputTSV)
        find_missing_rows(maindict, curationdict, curationTSV, data_type_column)
    except:
        create_curation_TSV(inputTSV, curationTSV, data_type_column)
