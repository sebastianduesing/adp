# This script judges the confidence of auto- and manually-curated values in the interpreted TSV.
# Arguments: input TSV, output TSV.

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


confByType = {
    "range": 85,
    "exact": 90,
    "null": 100,
    "exact_comment": 80,
    "comment": 80,
    "lower_limit": 90,
    "upper_limit": 90,
    "range_with_mean": 85,
    "other": 40
}


def unitConfidence(unit, confidence):
    if unit == "":
        pass
    elif unit in ["year", "week", "day", "month", "hour"]:
        confidence = confidence*1.1
    else:
        confidence = confidence*0.25
    return confidence


def judgeConfidence(xdict):
    for index, row in xdict.items():
        rowtype = row["age_type"]
        confidence = confByType[rowtype]
        unit = row["age_unit"]
        confidence = unitConfidence(unit, confidence)
        row["confidence"] = confidence
        if row["confidence"] > 100:
            row["confidence"] == 100
    return xdict


if __name__ == "__main__":
    maindict = dictFromTSV(sys.argv[1])  # typed TSV path
    newdict = judgeConfidence(maindict)
    dictToTSV(newdict, sys.argv[2])  # output path
