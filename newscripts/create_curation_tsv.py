import sys
from converter import TSV2dict, dict2TSV


def create_curation_TSV(input_path, output_path, data_type_column):
    curation_dict = {}
    maindict = TSV2dict(input_path)
    for index, rowdict in maindict.items():
        if rowdict[data_type_column] == "":
            curation_dict[index] = rowdict
            curation_dict[index][data_type_column] = "other"
    dict2TSV(curation_dict, output_path)


if __name__ == "__main__":
    inputTSV = sys.argv[1]
    outputTSV = sys.argv[2]
    data_type_column = sys.argv[3]
    create_curation_TSV(inputTSV, outputTSV, data_type_column)
