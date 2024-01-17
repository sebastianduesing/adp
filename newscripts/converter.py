import csv


def TSV2dict(path):
    """
    Makes a dict out of a TSV input and returns it. The output dict has indices
    for keys and dicts for the corresponding row of data as its values. Those
    dicts have column headers as their keys and the data in those columns
    for the values.

    -- path: Path of TSV to be turned into a dict.
    -- Returns the dict.
    """
    with open(path, "r", encoding="UTF-8") as infile:
        reader = csv.DictReader(infile, delimiter="\t")
        data = {}
        newindex = 0
        for row in reader:
            if "index" not in row:
                data[newindex] = {}
                for i in row:
                    data[newindex][i] = row[i]
                data[newindex]["index"] = newindex
                newindex += 1
            else:
                index = int(row["index"])
                data[index] = {}
                for i in row:
                    data[index][i] = row[i]
        count = len(data.keys())
        print(f"{count} rows added from TSV to dict.")
        return data


def dict2TSV(xdict, path):
    """
    Makes a TSV from a dict input in the format created by TSV2dict.

    -- xdict: Name of the dict to be turned into a TSV.
    -- path: Path of output TSV.
    """
    indices = [i for i in xdict.keys()]
    first = indices[0]
    fieldnames = [i for i in xdict[first].keys()]
    with open(path, "w", newline="\n") as tsv:
        writer = csv.DictWriter(tsv, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for (index, row) in xdict.items():
            writer.writerow(row)
        print(f"{path} written and saved.")
