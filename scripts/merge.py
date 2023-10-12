# This script merges data in a manually curated TSV into a sorted TSV and removes it from
# an unsorted TSV.
# args: [1] curated_tsv [2] sorted_tsv [3] unsorted_tsv [4] merged_sorted_tsv [5] merged_unsorted_tsv


import csv
import sys


def dictFromTSV(path):
    with open(path, "r", encoding="UTF-8") as infile:
        reader = csv.DictReader(infile, delimiter="\t")
        data = {}
        for row in reader:
            index = int(row["index"])
            data[index] = {}
            for i in row:
                data[index][i] = row[i]
        count = len(data.keys())
        print(f"{count} rows added from TSV to dict.")
        return data


def dictToTSV(xdict, path):
    indices = [i for i in xdict.keys()]
    first = indices[0]
    fieldnames = [i for i in xdict[first].keys()]
    with open(path, "w", newline="\n") as tsv:
        writer = csv.DictWriter(tsv, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for (index, row) in xdict.items():
            writer.writerow(row)
        print(f"{path} written and saved.")


def merge(curatedDict, sortedDict, unsortedDict):
    for (index, row) in curatedDict.items():
        sortedDict[index] = row
        del unsortedDict[index]
    return curatedDict, sortedDict, unsortedDict


if __name__ == "__main__":
    cd = dictFromTSV(sys.argv[1])  # curated tsv path
    sd = dictFromTSV(sys.argv[2])  # sorted tsv path
    ud = dictFromTSV(sys.argv[3])  # unsorted path

    cd, sd, ud = merge(cd, sd, ud)

    dictToTSV(sd, sys.argv[4])  # merged-sorted tsv path
    dictToTSV(ud, sys.argv[5])  # merged-unsorted tsv path
