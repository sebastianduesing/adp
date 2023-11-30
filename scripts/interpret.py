# This script adds the "age_type" and "age_readable" columns to the merged TSV.

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


def integerize(num):
    if type(num) == float:
        intnum = int(num)
        if intnum == num:
            num = intnum
    if type(num) == str and num != "":
        floatnum = float(num)
        intnum = int(floatnum)
        if intnum == floatnum:
            num = intnum
        else:
            num = floatnum
    return num


def typeAge(xdict):
    typeDict = {
        "exact": [True, False, False, False],
        "exact_comment": [True, False, False, True],
        "comment": [False, False, False, True],
        "range": [False, True, True, False],
        "lower_limit": [False, True, False, False],
        "upper_limit": [False, False, True, False],
        "range_with_mean": [True, True, True, True],
        "null": [False, False, False, False]
    }
    for index, row in xdict.items():
        row["age_type"] = "other"
        conditions = [
            row["age_specified"] != "",
            row["age_minimum"] != "",
            row["age_maximum"] != "",
            row["age_comment"] != ""
        ]
        for ageType, typeConditions in typeDict.items():
            if conditions == typeConditions:
                row["age_type"] = ageType
    return xdict


def makeReadable(xdict):
    for index, row in xdict.items():
        age_exact = row["age_specified"]
        age_exact = integerize(age_exact)
        age_min = row["age_minimum"]
        age_min = integerize(age_min)
        age_max = row["age_maximum"]
        age_max = integerize(age_max)
        unit = row["age_unit"]
        if age_exact != 1:
            if unit != "":
                unit = f"{unit}s"
        comment = row["age_comment"]
        agetype = row["age_type"]
        formatDict = {
            "exact": f"""{age_exact}{f" {unit}"if unit != "" else ""}""",
            "exact_comment": f"""{age_exact}{f" {unit}" if unit != "" else ""} ({comment})""",
            "comment": f"""{comment}""",
            "range": f"""{age_min}-{age_max}{f" {unit}" if unit != "" else ""}""",
            "lower_limit": f""">{age_min}{f" {unit}" if unit != "" else ""}""",
            "upper_limit": f"""<{age_max}{f" {unit}" if unit != "" else ""}""",
            "range_with_mean": f"""{age_min}-{age_max}{f" {unit}" if unit != "" else ""} ({comment}: {age_exact}{f" {unit}" if unit != "" else ""})""",
            "other": "",
            "null": "null"
        }
        format = formatDict[agetype]
        row["age_readable"] = format
    return xdict
        

if __name__ == "__main__":
    maindict = dictFromTSV(sys.argv[1])  # merged TSV path
    typedDict = typeAge(maindict)
    makeReadable(maindict)
    dictToTSV(typedDict, sys.argv[2])  # output path