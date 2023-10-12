# This script creates a TSV of only the curated rows from age_manual, the manual curation TSV.
# args: [1] age_manual [2] curated_tsv

import csv
import sys


def makeManualDict(inputTSV):
    with open(inputTSV, "r", encoding="UTF-8") as infile:
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


def findCuratedRows(manualDict):
    curatedDict = {}
    for i in manualDict.keys():
        row = manualDict[i]
        conditions = [
            row["age_specified"] != "",
            row["age_minimum"] != "",
            row["age_maximum"] != "",
            row["age_unit"] != "",
            row["age_comment"] != ""
        ]
        if any(conditions):
            curatedDict[i] = row
    count = len(curatedDict.keys())
    print(f"{count} rows added to curated row dict.")
    return curatedDict


def makeReference(curatedDict, referencePath):
    indices = [i for i in curatedDict.keys()]
    first = indices[0]
    fieldnames = [i for i in curatedDict[first].keys()]
    with open(referencePath, "w", newline="\n") as tsv:
        writer = csv.DictWriter(tsv, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for (index, row) in curatedDict.items():
            writer.writerow(row)
        print(f"{referencePath} written and saved.")


if __name__ == "__main__":
    manually_sorted = sys.argv[1]
    reference_path = sys.argv[2]
    md = makeManualDict(manually_sorted)
    cd = findCuratedRows(md)
    makeReference(cd, reference_path)
