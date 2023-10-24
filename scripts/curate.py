# This script checks unsorted data against a reference manually-curated TSV and sorts it
# based on the reference, outputting a merged TSV including all data and a TSV with
# all data that couldn't be sorted based on reference TSV.
# args: [1] reference TSV [2] sorted TSV [3] unsorted TSV [4] merged TSV [5] unsortable TSV

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


def sortDictByIndex(xdict):
    newdict = {}
    indices = []
    for i in xdict.keys():
        indices.append(i)
    indices = sorted(indices)
    for i in indices:
        newdict[i] = xdict[i]
    return newdict


def merge(referenceDict, sortedDict, unsortedDict):
    mergedDict = sortedDict.copy()
    reverseDict = {}
    unsortableDict = {}
    datalist = [row["h_age"] for index, row in referenceDict.items()]
    for index in referenceDict.keys():
        data = referenceDict[index]["h_age"]
        reverseDict[data] = int(index)
    for index, row in unsortedDict.items():
        data = row["age_normalized"]
        if data in datalist:
            id = reverseDict[data]
            vals = referenceDict[id]
            row["age_specified"] = vals["age_specified"]
            row["age_minimum"] = vals["age_minimum"]
            row["age_maximum"] = vals["age_maximum"]
            row["age_unit"] = vals["age_unit"]
            row["age_comment"] = vals["age_comment"]
            mergedDict[index] = row
        else:
            unsortableDict[index] = row
    mergedDict = sortDictByIndex(mergedDict)
    return mergedDict, unsortableDict


if __name__ == "__main__":
    refDict = dictFromTSV(sys.argv[1])  # reference TSV path
    sortedDict = dictFromTSV(sys.argv[2])  # sorted TSV path
    unsortedDict = dictFromTSV(sys.argv[3])  # unsorted TSV path
    mergedDict, unsortableDict = merge(refDict, sortedDict, unsortedDict)
    dictToTSV(mergedDict, sys.argv[4])  # merged TSV path
    if len(unsortableDict.keys()) > 0:
        dictToTSV(unsortableDict, sys.argv[5])  # unsortable TSV path
